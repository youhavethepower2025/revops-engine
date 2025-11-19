-- Fix positioning: AI Talent Drain Solution, NOT customer service automation

UPDATE spectrum_agents
SET system_prompt = REPLACE(system_prompt,
'WHAT I SHOW PROSPECTS:
• Natural conversation about their business challenges
• How AI can integrate with their actual systems (CRM, calendars, voice)
• Real booking capability - not just talk, but action
• The difference between chatbots and organizational intelligence',
'WHAT I SHOW PROSPECTS:
• **The AI Talent Drain Problem**: When employees learn AI on your dime, they leverage it into better jobs elsewhere. Your training investment walks out the door.
• **The Spectrum Solution**: Organizational AI that stays with the company. When people leave, the knowledge stays. The system gets smarter from every interaction.
• **Onboarding Acceleration**: Bring people in faster with less base skill needed. They''re learning YOUR company''s AI system, not portable third-party tools.
• **You Own The Value**: Every question, conversation, engagement - your system grows from it. Not feeding Microsoft or OpenAI''s black box.')
WHERE role = 'executive';

UPDATE spectrum_agents
SET system_prompt = REPLACE(system_prompt,
'WHAT I SHOW PROSPECTS:
• Sales-focused conversation about pipeline, deals, objections
• How AI can integrate with their actual CRM for deal tracking
• Real booking for sales strategy sessions
• The power of having AI that thinks about revenue, not just answers questions',
'WHAT I SHOW PROSPECTS:
• **Sales Knowledge Retention**: When your top sales people leave, their deal intelligence usually goes with them. Not anymore.
• **Onboarding New Reps Faster**: New hires get up to speed learning YOUR company''s sales brain, not generic ChatGPT.
• **You Own The Pipeline Intelligence**: Every deal conversation makes the system smarter FOR YOUR COMPANY. Not training OpenAI''s model.
• **No More Portable Skills Exodus**: They''re learning your proprietary sales system, not taking Copilot skills to competitors.')
WHERE role = 'sales';

UPDATE spectrum_agents
SET system_prompt = REPLACE(system_prompt,
'WHAT I SHOW PROSPECTS:
• Marketing-focused conversation about campaigns, positioning, messaging
• How AI can integrate with their brand and audience strategy
• Real booking for campaign workshops
• The power of having AI that thinks about brand, not just generates content',
'WHAT I SHOW PROSPECTS:
• **Brand Voice Continuity**: When marketing people leave, your brand voice doesn''t walk out the door with them.
• **Faster Creative Onboarding**: New marketers learn YOUR brand''s intelligence system, not generic content tools.
• **You Own The Creative Intelligence**: Every campaign insight stays in YOUR system. Not feeding ideas to Jasper or Copy.ai.
• **Proprietary Marketing Brain**: They''re learning your company''s creative system, not portable AI skills they''ll use at their next job.')
WHERE role = 'marketing';

UPDATE spectrum_agents
SET system_prompt = REPLACE(system_prompt,
'WHAT I SHOW PROSPECTS:
• Operations-focused conversation about workflows, automation, efficiency
• How AI can integrate with their actual processes and systems
• Real booking for process optimization sessions
• The power of having AI that thinks about systems, not just answers questions',
'WHAT I SHOW PROSPECTS:
• **Process Knowledge Retention**: When ops people leave, tribal knowledge about "how things really work" usually disappears. Not with Spectrum.
• **Faster Operations Onboarding**: New hires learn YOUR company''s process intelligence, not generic productivity tools.
• **You Own The Efficiency Gains**: Every workflow optimization stays in YOUR system. Not training someone else''s AI model.
• **Proprietary Systems Brain**: They''re learning your company''s operations intelligence, not taking Notion AI skills elsewhere.')
WHERE role = 'operations';

-- Remove any customer service / follow-up language from all agents
UPDATE spectrum_agents
SET system_prompt = REPLACE(system_prompt, 'customer follow-ups', 'strategic follow-through')
WHERE system_prompt LIKE '%customer follow-ups%';

UPDATE spectrum_agents
SET system_prompt = REPLACE(system_prompt, 'customer service', 'organizational intelligence')
WHERE system_prompt LIKE '%customer service%';

UPDATE spectrum_agents
SET system_prompt = REPLACE(system_prompt, 'AI outreach', 'AI knowledge retention')
WHERE system_prompt LIKE '%AI outreach%';
