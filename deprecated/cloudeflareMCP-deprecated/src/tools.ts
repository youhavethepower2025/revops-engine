// MCP Tool Definitions - Available to ALL clients

import { MCPTool } from './types';

export const MCP_TOOLS: MCPTool[] = [
  // ============ MEMORY TOOLS ============
  {
    name: "remember",
    description: "Store a key-value pair in client's semantic memory",
    inputSchema: {
      type: "object",
      properties: {
        key: { type: "string", description: "Memory key" },
        value: { type: ["string", "object", "array"], description: "Value to store" },
        metadata: { type: "object", description: "Optional metadata" }
      },
      required: ["key", "value"]
    }
  },
  {
    name: "recall",
    description: "Retrieve a value from client's semantic memory",
    inputSchema: {
      type: "object",
      properties: {
        key: { type: "string", description: "Memory key to retrieve" }
      },
      required: ["key"]
    }
  },
  {
    name: "search_memory",
    description: "Search client's memory by query",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "Search query" },
        limit: { type: "number", description: "Max results", default: 10 }
      },
      required: ["query"]
    }
  },

  // ============ RETELL TOOLS ============
  {
    name: "retell_get_call",
    description: "Get details of a specific call",
    inputSchema: {
      type: "object",
      properties: {
        call_id: { type: "string", description: "Retell call ID" }
      },
      required: ["call_id"]
    }
  },
  {
    name: "retell_list_calls",
    description: "List recent calls for this client",
    inputSchema: {
      type: "object",
      properties: {
        limit: { type: "number", description: "Number of calls to retrieve", default: 10 },
        phone_number: { type: "string", description: "Filter by phone number" }
      }
    }
  },
  {
    name: "retell_create_phone_call",
    description: "Initiate an outbound call",
    inputSchema: {
      type: "object",
      properties: {
        agent_id: { type: "string", description: "Retell agent ID" },
        to_number: { type: "string", description: "Phone number to call" },
        from_number: { type: "string", description: "Caller ID number" },
        metadata: { type: "object", description: "Call metadata" }
      },
      required: ["agent_id", "to_number", "from_number"]
    }
  },
  {
    name: "retell_get_call_transcript",
    description: "Get full transcript of a call",
    inputSchema: {
      type: "object",
      properties: {
        call_id: { type: "string", description: "Retell call ID" }
      },
      required: ["call_id"]
    }
  },

  // ============ GHL CRM TOOLS ============
  {
    name: "ghl_search_contact",
    description: "Search for a contact by phone number or email",
    inputSchema: {
      type: "object",
      properties: {
        phone: { type: "string", description: "Phone number to search" },
        email: { type: "string", description: "Email to search" }
      }
    }
  },
  {
    name: "ghl_get_contact",
    description: "Get full contact details by ID",
    inputSchema: {
      type: "object",
      properties: {
        contact_id: { type: "string", description: "GHL contact ID" }
      },
      required: ["contact_id"]
    }
  },
  {
    name: "ghl_create_contact",
    description: "Create a new contact in GHL",
    inputSchema: {
      type: "object",
      properties: {
        firstName: { type: "string" },
        lastName: { type: "string" },
        email: { type: "string" },
        phone: { type: "string" },
        tags: { type: "array", items: { type: "string" } },
        customFields: { type: "object" }
      },
      required: ["phone"]
    }
  },
  {
    name: "ghl_update_contact",
    description: "Update an existing contact",
    inputSchema: {
      type: "object",
      properties: {
        contact_id: { type: "string" },
        firstName: { type: "string" },
        lastName: { type: "string" },
        email: { type: "string" },
        phone: { type: "string" },
        tags: { type: "array", items: { type: "string" } },
        customFields: { type: "object" }
      },
      required: ["contact_id"]
    }
  },
  {
    name: "ghl_create_opportunity",
    description: "Create a sales opportunity",
    inputSchema: {
      type: "object",
      properties: {
        contact_id: { type: "string" },
        name: { type: "string" },
        pipeline_id: { type: "string" },
        stage_id: { type: "string" },
        value: { type: "number" },
        status: { type: "string" }
      },
      required: ["contact_id", "name"]
    }
  },
  {
    name: "ghl_add_note",
    description: "Add a note to a contact",
    inputSchema: {
      type: "object",
      properties: {
        contact_id: { type: "string" },
        note: { type: "string" }
      },
      required: ["contact_id", "note"]
    }
  },
  {
    name: "ghl_create_appointment",
    description: "Create a calendar appointment",
    inputSchema: {
      type: "object",
      properties: {
        contact_id: { type: "string" },
        calendar_id: { type: "string" },
        start_time: { type: "string", description: "ISO 8601 timestamp" },
        end_time: { type: "string", description: "ISO 8601 timestamp" },
        title: { type: "string" }
      },
      required: ["contact_id", "calendar_id", "start_time", "end_time"]
    }
  },
  {
    name: "ghl_trigger_workflow",
    description: "Trigger a GHL workflow/automation",
    inputSchema: {
      type: "object",
      properties: {
        contact_id: { type: "string" },
        workflow_id: { type: "string" }
      },
      required: ["contact_id", "workflow_id"]
    }
  }
];
