import { apiClient } from "./auth-api";
import { refreshTokenIfNeeded } from "./api-interceptor";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface ChatMessage {
  role: string;
  content: string;
}

export interface StreamChatRequest {
  conversation_id: string;
  messages: ChatMessage[];
}

export interface StreamChatChunk {
  type: "message" | "tool_output" | "error";
  content: string;
  error?: string;
}

export interface StreamChatResponse {
  content: Array<{ type: "text" | "tool-call"; text: string; result?: string }>;
  role?: "assistant";
}

/**
 * Streaming chat API client that handles authentication and token refresh
 */
class StreamingChatApi {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = `${baseUrl}/api/v1`;
  }

  /**
   * Get authenticated headers for streaming requests
   */
  private getStreamingHeaders(): HeadersInit {
    const token = localStorage.getItem("access_token");
    return {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  /**
   * Make an authenticated streaming request with automatic token refresh
   */
  private async makeStreamingRequest(
    url: string,
    options: RequestInit
  ): Promise<Response> {
    // Ensure token is refreshed before making the request
    const tokenValid = await refreshTokenIfNeeded();
    if (!tokenValid) {
      throw new Error("Authentication expired. Please refresh the page and try again.");
    }

    let response = await fetch(url, {
      ...options,
      headers: {
        ...this.getStreamingHeaders(),
        ...options.headers,
      },
    });

    // Handle authentication errors with retry
    if (response.status === 401) {
      // Try to refresh token one more time
      const retryTokenValid = await refreshTokenIfNeeded();
      if (retryTokenValid) {
        response = await fetch(url, {
          ...options,
          headers: {
            ...this.getStreamingHeaders(),
            ...options.headers,
          },
        });
      }

      if (response.status === 401) {
        throw new Error("Authentication expired. Please refresh the page and try again.");
      }
    }

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response;
  }

  /**
   * Stream chat messages with proper authentication and error handling
   */
  async *streamChat(request: StreamChatRequest): AsyncGenerator<StreamChatResponse, void, unknown> {
    const url = `${this.baseUrl}/chat/stream`;
    
    let response: Response;
    try {
      response = await this.makeStreamingRequest(url, {
        method: "POST",
        body: JSON.stringify(request),
      });
    } catch (error) {
      console.error("Chat stream request failed:", error);
      yield {
        content: [
          {
            type: "text",
            text: `Connection error: ${error instanceof Error ? error.message : "Unknown error"}. Please try again.`,
          },
        ],
      };
      return;
    }

    if (!response.body) {
      yield {
        content: [
          {
            type: "text",
            text: "No response received. Please try again.",
          },
        ],
      };
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let accumulatedText = "";
    let lastYieldedText = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const json: StreamChatChunk = JSON.parse(line.substring(6));
              
              if (json.type === "message" && json.content) {
                accumulatedText += json.content;
                if (accumulatedText !== lastYieldedText) {
                  yield {
                    content: [{ type: "text", text: accumulatedText }],
                  };
                  lastYieldedText = accumulatedText;
                }
              } else if (json.type === "tool_output") {
                yield {
                  role: "assistant",
                  content: [
                    {
                      type: "tool-call",
                      text: json.content,
                      result: json.content,
                    },
                  ],
                };
              } else if (json.type === "error") {
                console.error("Stream error:", json.error);
                yield {
                  content: [
                    {
                      type: "text",
                      text: `An error occurred: ${json.error}`,
                    },
                  ],
                };
                return;
              }
            } catch (e) {
              // ignore parsing errors for malformed JSON chunks
            }
          }
        }
      }
    } catch (error) {
      console.error("Stream reading error:", error);
      yield {
        content: [
          {
            type: "text",
            text: "Connection interrupted. Please try sending your message again.",
          },
        ],
      };
    } finally {
      reader.releaseLock();
    }
  }
}

// Export singleton instance
export const streamingChatApi = new StreamingChatApi();

// Export convenience function
export const streamChatMessages = (request: StreamChatRequest) => 
  streamingChatApi.streamChat(request);
