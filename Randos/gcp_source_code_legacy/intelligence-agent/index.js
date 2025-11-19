const { Storage } = require('@google-cloud/storage');
const { google } = require('googleapis');
const axios = require('axios');

console.log('Intelligence Agent: Full process.env:', JSON.stringify(process.env, null, 2));

const storage = new Storage();
const PROJECT_ID = 'omnicall-464316';
const transcriptBucketName = 'omnicall-464316-transcripts';
const summariesDriveFolderId = '1WL12UP7pO9tFjcFw57YDgfCC-XQ98GuE';

exports.intelligenceAgent = async (cloudEvent) => {
  console.log('Intelligence Agent: Received raw CloudEvent:', JSON.stringify(cloudEvent, null, 2));
  console.log('Intelligence Agent: Function started.');

  try {
    // Authenticate with Google APIs.
    // By not specifying scopes, the client will inherit the scopes from the service account.
    console.log('Intelligence Agent: Authenticating for Google APIs.');
    const auth = new google.auth.GoogleAuth({});
    const authClient = await auth.getClient();
    google.options({ auth: authClient });
    console.log('Intelligence Agent: GoogleAuth client obtained.');

    const pubSubMessageData = Buffer.from(cloudEvent.data, 'base64').toString('utf8');
    const { transcriptFileName } = JSON.parse(pubSubMessageData);
    console.log(`Intelligence Agent: Processing transcript: ${transcriptFileName}`);

    const docTitle = `${transcriptFileName.replace('.txt', '')} - AI Summary`;

    // Check for existing summary to ensure idempotency
    const drive = google.drive({ version: 'v3', auth: authClient });
    const existingFiles = await drive.files.list({
      q: `name = '${docTitle}' and '${summariesDriveFolderId}' in parents and trashed = false`,
      fields: 'files(id, name)',
    });

    if (existingFiles.data.files.length > 0) {
      console.log(`Intelligence Agent: Summary for "${docTitle}" already exists. Skipping creation.`);
      return; // Exit function if summary already exists
    }

    console.log(`Intelligence Agent: Reading transcript from gs://${transcriptBucketName}/${transcriptFileName}`);
    const [transcriptContent] = await storage.bucket(transcriptBucketName).file(transcriptFileName).download();
    const transcript = transcriptContent.toString('utf8');
    console.log('Intelligence Agent: Transcript read successfully.');

    // Generate summary with Vertex AI
    console.log('Intelligence Agent: Generating summary with Vertex AI.');
    const accessToken = (await authClient.getAccessToken()).token;
    const vertexAiUrl = `https://us-central1-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/us-central1/publishers/google/models/gemini-2.5-flash:generateContent`;
    
    const request_body = {
      "contents": [{
        "role": "user",
        "parts": [{ "text": `Summarize this transcript: ${transcript}` }]
      }]
    };

    console.log('Intelligence Agent: Sending request to Vertex AI.');
    const vertexAiResponse = await axios.post(vertexAiUrl, request_body, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      }
    });

    const summary = vertexAiResponse.data.candidates[0].content.parts[0].text;
    console.log('Intelligence Agent: Summary generated successfully.');

    // Save summary to Google Drive
    const docs = google.docs({ version: 'v1', auth: authClient });

    console.log(`Intelligence Agent: Creating Google Doc with title: ${docTitle}`);
    const createDocResponse = await drive.files.create({
      requestBody: {
        name: docTitle,
        mimeType: 'application/vnd.google-apps.document',
        parents: [summariesDriveFolderId],
      },
      fields: 'id,name,parents',
    });
    const documentId = createDocResponse.data.id;
    console.log(`Intelligence Agent: Google Doc created with ID: ${documentId}`);

    console.log('Intelligence Agent: Updating Google Doc content.');
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
    console.log('Intelligence Agent: Google Doc content updated.');
    console.log(`Intelligence Agent: Summary saved to Google Drive: ${docTitle} (ID: ${documentId})`);

  } catch (err) {
    console.error('Intelligence Agent ERROR:', err.message);
    if (err.response) {
      console.error('Intelligence Agent ERROR Response Data:', JSON.stringify(err.response.data, null, 2));
    } else {
      console.error('Intelligence Agent FULL ERROR OBJECT:', JSON.stringify(err, null, 2));
    }
  }
};