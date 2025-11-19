const { Storage } = require('@google-cloud/storage');
const { google } = require('googleapis');
const axios = require('axios');

console.log('Opportunity Agent: Full process.env:', JSON.stringify(process.env, null, 2));

const storage = new Storage();
const PROJECT_ID = 'omnicall-464316';
const transcriptBucketName = 'omnicall-464316-transcripts';
const summariesDriveFolderId = '1WL12UP7pO9tFjcFw57YDgfCC-XQ98GuE';

exports.intelligenceAgent = async (cloudEvent) => {
  console.log('Opportunity Agent: Received raw CloudEvent:', JSON.stringify(cloudEvent, null, 2));
  console.log('Opportunity Agent: Function started.');

  try {
    const auth = new google.auth.GoogleAuth({});
    const authClient = await auth.getClient();
    google.options({ auth: authClient });
    console.log('Opportunity Agent: GoogleAuth client obtained.');

    const pubSubMessageData = Buffer.from(cloudEvent.data, 'base64').toString('utf8');
    const { transcriptFileName } = JSON.parse(pubSubMessageData);
    console.log(`Opportunity Agent: Processing transcript: ${transcriptFileName}`);

    const docTitle = `${transcriptFileName.replace('.txt', '')} - Revenue Opportunity Report`;

    const drive = google.drive({ version: 'v3', auth: authClient });
    const existingFiles = await drive.files.list({
      q: `name = '${docTitle}' and '${summariesDriveFolderId}' in parents and trashed = false`,
      fields: 'files(id, name)',
    });

    if (existingFiles.data.files.length > 0) {
      console.log(`Opportunity Agent: Summary for "${docTitle}" already exists. Skipping creation.`);
      return;
    }

    console.log(`Opportunity Agent: Reading transcript from gs://${transcriptBucketName}/${transcriptFileName}`);
    const [transcriptContent] = await storage.bucket(transcriptBucketName).file(transcriptFileName).download();
    const transcript = transcriptContent.toString('utf8');
    console.log('Opportunity Agent: Transcript read successfully.');

    console.log('Opportunity Agent: Generating summary with Vertex AI.');
    const accessToken = (await authClient.getAccessToken()).token;
    const vertexAiUrl = `https://us-central1-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/us-central1/publishers/google/models/gemini-2.5-flash:generateContent`;
    
    const prompt = `As a Senior Business Development Analyst, analyze the following transcript for upsell opportunities, customer pain points, and competitive intelligence. Provide a revenue opportunity report with actionable insights:

${transcript}`;

    const request_body = {
      "contents": [{
        "role": "user",
        "parts": [{ "text": prompt }]
      }]
    };

    console.log('Opportunity Agent: Sending request to Vertex AI.');
    const vertexAiResponse = await axios.post(vertexAiUrl, request_body, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      }
    });

    const summary = vertexAiResponse.data.candidates[0].content.parts[0].text;
    console.log('Opportunity Agent: Summary generated successfully.');

    const docs = google.docs({ version: 'v1', auth: authClient });

    console.log(`Opportunity Agent: Creating Google Doc with title: ${docTitle}`);
    const createDocResponse = await drive.files.create({
      requestBody: {
        name: docTitle,
        mimeType: 'application/vnd.google-apps.document',
        parents: [summariesDriveFolderId],
      },
      fields: 'id,name,parents',
    });
    const documentId = createDocResponse.data.id;
    console.log(`Opportunity Agent: Google Doc created with ID: ${documentId}`);

    console.log('Opportunity Agent: Updating Google Doc content.');
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
    console.log('Opportunity Agent: Google Doc content updated.');
    console.log(`Opportunity Agent: Summary saved to Google Drive: ${docTitle} (ID: ${documentId})`);

  } catch (err) {
    console.error('Opportunity Agent ERROR:', err.message);
    if (err.response) {
      console.error('Opportunity Agent ERROR Response Data:', JSON.stringify(err.response.data, null, 2));
    } else {
      console.error('Opportunity Agent FULL ERROR OBJECT:', JSON.stringify(err, null, 2));
    }
  }
};
