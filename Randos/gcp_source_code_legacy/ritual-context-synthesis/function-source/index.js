const { VertexAI } = require('@google-cloud/vertexai');
const { Firestore } = require('@google-cloud/firestore');
const { Storage } = require('@google-cloud/storage');
const sgMail = require('@sendgrid/mail');
const fs = require('fs').promises; // Use promises version of fs

// Lazy initialization for clients
let vertexAI, model, firestore, storage;

function initializeClients() {
    if (!firestore) firestore = new Firestore();
    if (!storage) storage = new Storage();
    // In a GCP environment, Project ID and Location are inferred automatically.
    if (!vertexAI) vertexAI = new VertexAI();
    if (!model) model = vertexAI.getGenerativeModel({ model: 'gemini-1.5-pro' });

    // Set SendGrid API Key from environment variable
    sgMail.setApiKey(process.env.SENDGRID_API_KEY);
}

exports.ritualContextSynthesis = async (cloudEvent) => {
  initializeClients();

  const callId = cloudEvent.params.callId;
  console.log(`Processing call: ${callId}`);

  const eventData = cloudEvent.data.value;
  if (!eventData || eventData.fields.status.stringValue !== 'completed') {
    console.log(`Call ${callId} status is not 'completed'. Skipping.`);
    return;
  }

  // Retrieve the full transcript from the subcollection
  const transcriptSnapshot = await firestore
    .collection('transcripts')
    .doc(callId)
    .collection('messages')
    .orderBy('timestamp')
    .get();

  if (transcriptSnapshot.empty) {
      console.log(`No transcript found for call ${callId}. Skipping.`);
      return;
  }

  const fullTranscript = transcriptSnapshot.docs
    .map(doc => `${doc.data().role}: ${doc.data().content}`)
    .join('\n');

  // 1. Generate Creative Brief
  const briefResponse = await model.generateContent(contextSynthesisPrompt(fullTranscript));
  const creativeBrief = briefResponse.response.text();

  const deliverableRef = await firestore.collection('deliverables').add({
    callId,
    type: 'creative_brief',
    content: creativeBrief,
    createdAt: new Date()
  });
  console.log(`Stored deliverable in Firestore with ID: ${deliverableRef.id}`);

  const bucketName = `ritual-deliverables-${process.env.GCLOUD_PROJECT}`;
  const bucket = storage.bucket(bucketName);
  const briefFileName = `${callId}/creative-brief-${deliverableRef.id}.md`;
  const briefFile = bucket.file(briefFileName);
  await briefFile.save(creativeBrief);
  console.log(`Creative Brief saved to gs://${bucketName}/${briefFileName}`);

  // 2. Perform Information Extraction
  let extractedData = {};
  try {
      const extractionPromptTemplate = await fs.readFile('/workspace/prompts/backend_extraction_prompt.md', 'utf8');
      const extractionPrompt = `${extractionPromptTemplate}\n\n## Transcript to Analyze:\n${fullTranscript}\n\n## Output Format:\n${JSON.stringify({
        "contact": {
          "name": "",
          "email": "",
          "phone": "",
          "company": ""
        },
        "organizationType": "",
        "platforms": [],
        "product": {
          "name": "",
          "description": ""
        },
        "audience": {
          "demographics": "",
          "psychographics": "",
          "painPoints": "",
          "desires": ""
        },
        "customerBehavior": {
          "dailyRoutine": "",
          "decisionProcess": "",
          "purchaseTriggers": ""
        },
        "budget": {
          "productionRange": "",
          "specificAmount": "",
          "adSpend": "",
          "needsMediaBuying": ""
        },
        "timeline": {
          "launchDate": "",
          "urgency": ""
        },
        "creative": {
          "approach": "",
          "videoStyle": "",
          "tone": ""
        },
        "talent": {
          "needsSpokesperson": "",
          "characterDescription": "",
          "voiceoverOnly": ""
        },
        "objectives": {
          "primaryGoal": "",
          "specificAction": "",
          "successMetrics": "",
          "emotionalOutcome": ""
        },
        "additionalContext": {
          "competitorReferences": "",
          "uniqueSellingPoints": "",
          "brandValues": "",
          "challenges": ""
        },
        "nextSteps": {
          "interestLevel": "",
          "followUpActions": "",
          "concerns": ""
        },
        "callQuality": {
          "informationCompleteness": "Score 1-10",
          "readyForConcepts": "Yes/No",
          "missingCriticalInfo": []
        }
      }, null, 2)}
      `;
      const extractionResponse = await model.generateContent(extractionPrompt);
      const extractionText = extractionResponse.response.text();
      try {
          extractedData = JSON.parse(extractionText);
          console.log("Successfully extracted structured data.");
      } catch (parseError) {
          console.error("Error parsing extracted JSON:", parseError);
          console.error("Raw extraction text:", extractionText);
      }
  } catch (error) {
      console.error("Error during information extraction:", error);
  }

  // 3. Prepare and Send Email
  try {
      const emailTemplate = await fs.readFile('/workspace/prompts/ritual_team_email_template.md', 'utf8');
      let emailSubject = `New Creative Brief - ${extractedData.contact?.company || '[Company Name]'} - ${extractedData.product?.name || '[Product Name]'} - ${extractedData.budget?.productionRange || '[Budget Range]'}`;
      
      let emailBody = emailTemplate
          .replace(/\[Contact Name\]/g, extractedData.contact?.name || 'Not specified')
          .replace(/\[Company Name\]/g, extractedData.contact?.company || 'Not specified')
          .replace(/\[Email\]/g, extractedData.contact?.email || 'Not specified')
          .replace(/\[Phone\]/g, extractedData.contact?.phone || 'Not specified')
          .replace(/\[Organization Type\]/g, extractedData.organizationType || 'Not specified')
          .replace(/\[Product Name\]/g, extractedData.product?.name || 'Not specified')
          .replace(/\[Product Description\]/g, extractedData.product?.description || 'Not specified')
          .replace(/\[What they want to achieve\]/g, extractedData.objectives?.primaryGoal || 'Not specified')
          .replace(/\[What viewers should do\]/g, extractedData.objectives?.specificAction || 'Not specified')
          .replace(/\[How viewers should feel\]/g, extractedData.objectives?.emotionalOutcome || 'Not specified')
          .replace(/\[How they'll measure success\]/g, extractedData.objectives?.successMetrics || 'Not specified')
          .replace(/\[Age, gender, location, income details\]/g, extractedData.audience?.demographics || 'Not specified')
          .replace(/\[Values, interests, lifestyle details\]/g, extractedData.audience?.psychographics || 'Not specified')
          .replace(/\[What problems they face\]/g, extractedData.audience?.painPoints || 'Not specified')
          .replace(/\[When they need the product\]/g, extractedData.customerBehavior?.dailyRoutine || 'Not specified')
          .replace(/\[How they evaluate options\]/g, extractedData.customerBehavior?.decisionProcess || 'Not specified')
          .replace(/\[What motivates them to buy\]/g, extractedData.customerBehavior?.purchaseTriggers || 'Not specified')
          .replace(/\[Budget Range\]/g, extractedData.budget?.productionRange || 'Not specified')
          .replace(/\[If mentioned\]/g, extractedData.budget?.specificAmount || 'Not specified')
          .replace(/\[Media buying budget\]/g, extractedData.budget?.adSpend || 'Not specified')
          .replace(/\[Needs Media Buying Services\]/g, extractedData.budget?.needsMediaBuying || 'Not specified')
          .replace(/\[Target date\]/g, extractedData.timeline?.launchDate || 'Not specified')
          .replace(/\[Urgency Level\]/g, extractedData.timeline?.urgency || 'Not specified')
          .replace(/\[List all platforms: TikTok, Instagram, YouTube, etc.\]/g, extractedData.platforms?.join(', ') || 'Not specified')
          .replace(/\[Creative Approach\]/g, extractedData.creative?.approach || 'Not specified')
          .replace(/\[Video Style\]/g, extractedData.creative?.videoStyle || 'Not specified')
          .replace(/\[Tone\]/g, extractedData.creative?.tone || 'Not specified')
          .replace(/\[Need Spokesperson\]/g, extractedData.talent?.needsSpokesperson || 'Not specified')
          .replace(/\[Character Description\]/g, extractedData.talent?.characterDescription || 'Not specified')
          .replace(/\[Voiceover Only\]/g, extractedData.talent?.voiceoverOnly || 'Not specified')
          .replace(/\[Examples mentioned\]/g, extractedData.additionalContext?.competitorReferences || 'Not specified')
          .replace(/\[Brands or campaigns mentioned\]/g, extractedData.additionalContext?.competitorReferences || 'Not specified')
          .replace(/\[What makes them special\]/g, extractedData.additionalContext?.uniqueSellingPoints || 'Not specified')
          .replace(/\[Core principles or mission\]/g, extractedData.additionalContext?.brandValues || 'Not specified')
          .replace(/\[Marketing obstacles they face\]/g, extractedData.additionalContext?.challenges || 'Not specified')
          .replace(/\[Impactful quote 1\]/g, '' /* Placeholder for actual quotes */)
          .replace(/\[Impactful quote 2\]/g, '' /* Placeholder for actual quotes */)
          .replace(/\[Interest Level\]/g, extractedData.nextSteps?.interestLevel || 'Not specified')
          .replace(/\[What was agreed upon\]/g, extractedData.nextSteps?.followUpActions || 'Not specified')
          .replace(/\[Any hesitations or additional info needed\]/g, extractedData.nextSteps?.concerns || 'Not specified')
          .replace(/\[Score 1-10\]/g, extractedData.callQuality?.informationCompleteness || 'Not specified')
          .replace(/\[List any gaps\]/g, extractedData.callQuality?.missingCriticalInfo?.join(', ') || 'None')
          .replace(/\[Include the full JSON extraction here for technical reference\]/g, JSON.stringify(extractedData, null, 2))
          .replace(/\[Link to recording if available\]/g, `https://console.cloud.google.com/storage/browser/${bucketName}/${callId}/`)
          .replace(/\[Link to full transcript\]/g, `https://console.cloud.google.com/firestore/data/conversations/${callId}/transcripts/${callId}/messages`)
          .replace(/\[Date\]/g, new Date().toLocaleDateString())
          .replace(/\[Name of CD who took the call\]/g, 'AI Creative Director') // Placeholder
          .replace(/\[High\/Needs Follow-up\]/g, extractedData.callQuality?.readyForConcepts || 'Not specified')
          .replace(/\[Immediate\/Standard\/Flexible\]/g, extractedData.timeline?.urgency || 'Not specified')
          .replace(/\[Specific recommendation based on their needs\]/g, '' /* AI generated recommendation */)
          .replace(/\[Type of director who would be ideal\]/g, '' /* AI generated director type */)
          .replace(/\[What to emphasize in concepts\]/g, '' /* AI generated emphasis */)
          .replace(/\[What to watch out for\]/g, '' /* AI generated challenges */);

      // Replace the subject line placeholder as well
      emailSubject = emailSubject
          .replace(/\[Company Name\]/g, extractedData.contact?.company || '[Company Name]')
          .replace(/\[Product Name\]/g, extractedData.product?.name || '[Product Name]')
          .replace(/\[Budget Range\]/g, extractedData.budget?.productionRange || '[Budget Range]');

      const msg = {
          to: process.env.JETHRO_EMAIL_RECIPIENT, // Jethro's email recipient
          from: process.env.SENDER_EMAIL, // Your verified SendGrid sender email
          subject: emailSubject,
          html: emailBody,
      };
      await sgMail.send(msg);
      console.log(`Email sent to ${process.env.JETHRO_EMAIL_RECIPIENT}`);

  } catch (error) {
      console.error("Error preparing or sending email:", error);
  }
};

function contextSynthesisPrompt(transcript) {
  return `# Ritual Ads Context Synthesis Engine\n\n  **Objective**: Analyze the provided call transcript and generate a concise, actionable Creative Brief for an advertising campaign.\n\n  **Input**: Raw call transcript.\n\n  **Output**: A structured markdown document with the following sections:\n  - **Client**: [Client's Name]\n  - **Product/Service**: [Product or Service Discussed]\n  - **Key Pain Points**: [List 2-3 primary problems the client is facing]\n  - **Core Message**: [A single, powerful sentence that addresses the pain points]\n  - **Target Audience**: [Describe the ideal customer]\n  - **Call to Action**: [What should the ad ask the audience to do?]\n  - **Tone & Style**: [e.g., Professional, Humorous, Urgent]\n\n  ---\n  **TRANSCRIPT:**\n  ${transcript}\n  ---`;
}