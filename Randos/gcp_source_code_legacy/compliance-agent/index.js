const { Storage } = require('@google-cloud/storage');
const { google } = require('googleapis');
const axios = require('axios');

console.log('Compliance Agent: Full process.env:', JSON.stringify(process.env, null, 2));

const storage = new Storage();
const PROJECT_ID = 'omnicall-464316';
const transcriptBucketName = 'omnicall-464316-transcripts';
const summariesDriveFolderId = '1WL12UP7pO9tFjcFw57YDgfCC-XQ98GuE';

exports.intelligenceAgent = async (cloudEvent) => {
  console.log('Compliance Agent: Received raw CloudEvent:', JSON.stringify(cloudEvent, null, 2));
  console.log('Compliance Agent: Function started.');

  try {
    const auth = new google.auth.GoogleAuth({});
    const authClient = await auth.getClient();
    google.options({ auth: authClient });
    console.log('Compliance Agent: GoogleAuth client obtained.');

    const pubSubMessageData = Buffer.from(cloudEvent.data, 'base64').toString('utf8');
    const { transcriptFileName } = JSON.parse(pubSubMessageData);
    console.log(`Compliance Agent: Processing transcript: ${transcriptFileName}`);

    const docTitle = `${transcriptFileName.replace('.txt', '')} - Compliance Report`;

    const drive = google.drive({ version: 'v3', auth: authClient });
    const existingFiles = await drive.files.list({
      q: `name = '${docTitle}' and '${summariesDriveFolderId}' in parents and trashed = false`,
      fields: 'files(id, name)',
    });

    if (existingFiles.data.files.length > 0) {
      console.log(`Compliance Agent: Summary for "${docTitle}" already exists. Skipping creation.`);
      return;
    }

    console.log(`Compliance Agent: Reading transcript from gs://${transcriptBucketName}/${transcriptFileName}`);
    const [transcriptContent] = await storage.bucket(transcriptBucketName).file(transcriptFileName).download();
    const transcript = transcriptContent.toString('utf8');
    console.log('Compliance Agent: Transcript read successfully.');

    console.log('Compliance Agent: Generating summary with Vertex AI.');
    const accessToken = (await authClient.getAccessToken()).token;
    const vertexAiUrl = `https://us-central1-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/us-central1/publishers/google/models/gemini-2.5-flash:generateContent`;
    
    const prompt = `As a Senior Compliance Officer, analyze the following transcript for regulatory compliance, risk assessment, and policy violations. Provide a compliance report highlighting any concerns and recommendations:

${transcript}`;

    const request_body = {
      "contents": [{
        "role": "user",
        "parts": [{ "text": prompt }]
      }]
    };

    console.log('Compliance Agent: Sending request to Vertex AI.');
    const vertexAiResponse = await axios.post(vertexAiUrl, request_body, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      }
    });

    const summary = vertexAiResponse.data.candidates[0].content.parts[0].text;
    console.log('Compliance Agent: Summary generated successfully.');

    const docs = google.docs({ version: 'v1', auth: authClient });

    console.log(`Compliance Agent: Creating Google Doc with title: ${docTitle}`);
    const createDocResponse = await drive.files.create({
      requestBody: {
        name: docTitle,
        mimeType: 'application/vnd.google-apps.document',
        parents: [summariesDriveFolderId],
      },
      fields: 'id,name,parents',
    });
    const documentId = createDocResponse.data.id;
    console.log(`Compliance Agent: Google Doc created with ID: ${documentId}`);

    console.log('Compliance Agent: Updating Google Doc content.');
    await docs.documents.batchUpdate({
      documentId: documentId,
      requestBody: {
        requests: [{
          insertText: {
            text: summary,
            location: { index: 1 },
          },
        }],
      },
    });
    console.log('Compliance Agent: Google Doc content updated.');
    console.log(`Compliance Agent: Summary saved to Google Drive: ${docTitle} (ID: ${documentId})`);

  } catch (err) {
    console.error('Compliance Agent ERROR:', err.message);
    if (err.response) {
      console.error('Compliance Agent ERROR Response Data:', JSON.stringify(err.response.data, null, 2));
    } else {
      console.error('Compliance Agent FULL ERROR OBJECT:', JSON.stringify(err, null, 2));
    }
  }
};
