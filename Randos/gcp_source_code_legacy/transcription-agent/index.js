const { SpeechClient } = require('@google-cloud/speech');
const { Storage } = require('@google-cloud/storage');
const { PubSub } = require('@google-cloud/pubsub');
const { exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

const speechClient = new SpeechClient();
const storage = new Storage();
const pubsub = new PubSub();

const transcriptBucketName = 'omnicall-464316-transcripts';
const topicName = 'transcription-complete';
const tempAudioBucketName = 'omnicall-464316-transcripts'; // Using the same bucket for temp audio

exports.transcriptionAgent = async (cloudEvent) => {
  console.log('Transcription agent triggered!');
  console.log('Raw event object:', JSON.stringify(cloudEvent, null, 2));

  let bucketName;
  let fileName;
  let contentType;

  // Try to extract from different possible locations in cloudEvent
  if (cloudEvent.bucket && cloudEvent.name && cloudEvent.contentType) {
    bucketName = cloudEvent.bucket;
    fileName = cloudEvent.name;
    contentType = cloudEvent.contentType;
  } else if (cloudEvent.data && cloudEvent.data.bucket && cloudEvent.data.name && cloudEvent.data.contentType) {
    bucketName = cloudEvent.data.bucket;
    fileName = cloudEvent.data.name;
    contentType = cloudEvent.data.contentType;
  } else if (cloudEvent.data && cloudEvent.data.protoPayload && cloudEvent.data.protoPayload.resource && cloudEvent.data.protoPayload.resource.labels) {
    bucketName = cloudEvent.data.protoPayload.resource.labels.bucket_name;
    fileName = cloudEvent.data.protoPayload.resource.labels.file_name;
    // Content type is not directly available here, will infer from extension later
  }

  if (!bucketName || !fileName) {
    console.error('Error: Missing bucketName or fileName in cloudEvent. Could not extract necessary information.');
    return;
  }

  const fileExtension = path.extname(fileName).toLowerCase();
  const baseFileName = path.basename(fileName, fileExtension);

  console.log(`Processing file: ${fileName} from bucket: ${bucketName}`);

  let gcsUri = `gs://${bucketName}/${fileName}`;
  let localFilePath = `/tmp/${fileName}`;
  let audioGcsUri = '';
  let audioLocalPath = '';

  try {
    // Infer content type if not directly available
    if (!contentType) {
      if (fileExtension === '.mp4' || fileExtension === '.mov' || fileExtension === '.avi') {
        contentType = 'video/mp4';
      } else if (fileExtension === '.flac' || fileExtension === '.wav' || fileExtension === '.mp3') {
        contentType = 'audio/flac';
      } else {
        contentType = 'application/octet-stream'; // Default if unknown
      }
    }

    if (contentType.startsWith('video/') || !contentType.startsWith('audio/')) {
      console.log(`Extracting audio from video/non-audio file: ${fileName}`);

      // Download the video file
      console.log(`Downloading ${gcsUri} to ${localFilePath}`);
      await storage.bucket(bucketName).file(fileName).download({ destination: localFilePath });
      console.log(`Downloaded ${fileName} to ${localFilePath}`);

      // Extract audio using ffmpeg
      audioLocalPath = `/tmp/${baseFileName}.flac`;
      console.log(`Extracting audio from ${localFilePath} to ${audioLocalPath} using ffmpeg`);
      const ffmpegCommand = `ffmpeg -i "${localFilePath}" -vn -acodec flac -ar 16000 -sample_fmt s16 -ac 1 "${audioLocalPath}"`; // -ac 1 for mono
      
      await new Promise((resolve, reject) => {
        exec(ffmpegCommand, (error, stdout, stderr) => {
          if (error) {
            console.error(`FFmpeg error: ${error.message}`);
            console.error(`FFmpeg stdout: ${stdout}`);
            console.error(`FFmpeg stderr: ${stderr}`);
            return reject(error);
          }
          console.log(`FFmpeg stdout: ${stdout}`);
          console.log(`FFmpeg stderr: ${stderr}`);
          resolve();
        });
      });
      console.log(`Audio extracted to ${audioLocalPath}`);

      // Upload the extracted audio to GCS
      audioGcsUri = `gs://${tempAudioBucketName}/temp_audio/${baseFileName}.flac`;
      console.log(`Uploading ${audioLocalPath} to ${audioGcsUri}`);
      await storage.bucket(tempAudioBucketName).upload(audioLocalPath, { destination: `temp_audio/${baseFileName}.flac` });
      console.log(`Uploaded ${audioLocalPath} to ${audioGcsUri}`);
      gcsUri = audioGcsUri; // Use the audio GCS URI for transcription
    } else if (contentType.startsWith('audio/')) {
      console.log(`Processing audio file: ${fileName}`);
      // For audio files, directly use the GCS URI
    } else {
      console.log(`Skipping non-audio/non-video file: ${fileName}`);
      return;
    }

    const audio = {
      uri: gcsUri,
    };

    const config = {
      encoding: 'FLAC', // Set encoding to FLAC as we are converting to FLAC
      sampleRateHertz: 16000,
      languageCode: 'en-US',
      enableAutomaticPunctuation: true,
      // audioChannelCount: 2, // Removed to allow default or auto-detection
    };

    const request = {
      audio: audio,
      config: config,
    };

    // Start the long-running recognition operation
    const [operation] = await speechClient.longRunningRecognize(request);
    const [response] = await operation.promise();

    const transcription = response.results
      .map(result => result.alternatives[0].transcript)
      .join('\n');

    const transcriptFileName = `${baseFileName}.txt`;
    await storage.bucket(transcriptBucketName).file(transcriptFileName).save(transcription);
    console.log(`Transcript uploaded to gs://${transcriptBucketName}/${transcriptFileName}`);
    console.log(`Transcription complete for ${fileName}`);

    // Publish a message to the 'transcription-complete' topic
    const dataBuffer = Buffer.from(JSON.stringify({ transcriptFileName }));
    await pubsub.topic(topicName).publishMessage({ data: dataBuffer });
    console.log(`Published message to transcription-complete: ${transcriptFileName}`);

  } catch (err) {
    console.error('ERROR:', err);
  } finally {
    // Clean up temporary local files
    if (localFilePath && await fs.access(localFilePath).then(() => true).catch(() => false)) {
      await fs.unlink(localFilePath);
      console.log(`Cleaned up temporary local file: ${localFilePath}`);
    }
    if (audioLocalPath && await fs.access(audioLocalPath).then(() => true).catch(() => false)) {
      await fs.unlink(audioLocalPath);
      console.log(`Cleaned up temporary local audio file: ${audioLocalPath}`);
    }

    // Clean up temporary GCS FLAC file
    if (audioGcsUri) {
      const tempAudioFileName = audioGcsUri.split('/').pop();
      try {
        await storage.bucket(tempAudioBucketName).file(`temp_audio/${tempAudioFileName}`).delete();
        console.log(`Cleaned up temporary GCS FLAC file: ${audioGcsUri}`);
      } catch (deleteErr) {
        console.error(`Failed to clean up GCS FLAC file: ${deleteErr.message}`);
      }
    }
  }
};