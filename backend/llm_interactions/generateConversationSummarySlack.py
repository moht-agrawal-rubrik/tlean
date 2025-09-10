import os
from openai import OpenAI
from typing import List, Optional, Dict
from typing_extensions import Literal
from dataclasses import dataclass
from datetime import datetime



@dataclass
class SlackMessage:
    """
    Data structure representing a Slack message in a conversation.
    """
    messageId: str # backend
    timestamp: datetime
    sender: str
    content: str
    isReply: bool = False
    inReplyToMessageId: Optional[str] = None
    mentions: List[str] = None

    # Additional fields
    threadId: Optional[str] = None # optional to group messages for better context
    type: Literal["message", "system", "notification"] = "message"
    isActionItem: bool = False # if we can pre-populate this - it can be an early AI-assisted flagging mechanism
    hasLinks: bool = False # useful for cases when someone says - "it's being discussed here"
    links: List[str] = None
    reactions: List[str] = None # soft responses
    # relatedResources: List[Dict[str, str]] = None # for links -> le's ignore this now
    conversationTags: List[str] = None
    
    def __post_init__(self):
        if self.mentions is None:
            self.mentions = []


class ConversationSummaryGenerator:
    """
    A class to generate conversation summaries from Slack messages using LLM.
    """
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"), 
            base_url="https://basecamp.stark.rubrik.com"
        )
    
    def generate_conversation_summary(self, conversation: List[SlackMessage]) -> str:
        if not conversation:
            return "No messages to summarize."
        
        conversation_text = self._format_conversation_for_llm(conversation)
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are a highly capable assistant designed to summarize Slack conversations and extract actionable insights.
The input will be provided as a JSON object representing a list of Slack messages. Your job is to analyze this JSON object in detail and provide structured responses in a JSON format as output.

The input JSON object will consist of Slack messages, and each message will adhere to the following structure:

**SlackMessage Data Structure**:
- **`messageId`** (string): The unique identifier for the message. This helps trace replies and reconstruct the conversation thread.
- **`timestamp`** (datetime): The timestamp when the message was sent. This enables chronological ordering and understanding the evolution of the discussion.
- **`sender`** (string): The username or identifier of the person who sent the message. This is used for attribution and understanding who is responsible for key points and actions.
- **`content`** (string): The actual text of the Slack message. This is the main data you analyze to extract insights, including summarization, identifying problems, extracting links, and deriving action items. You have to also decide whether this message is a problem statement, a decision made, or an open question, or just some noise.
- **`isReply`** (boolean): Indicates whether the message is a reply to another message within a thread. This is useful for understanding sub-discussions within larger threads and grouping context accurately.
- **`inReplyToMessageId`** (string, optional): If the message is a reply, this field contains the `messageId` of the parent message. This helps reconstruct conversation hierarchies and understand dependencies between messages.
- **`mentions`** (list of strings, optional): A list of usernames or identifiers mentioned in the message. This is used to infer participants, task assignments, and involvement in specific parts of the discussion.
- **`threadId`** (string, optional): A unique identifier for the top-level thread to which this message belongs. This helps group messages and organize conversations when analyzing multiple threads.
- **`type`** (string, optional): Indicates the type of message (e.g., 'message', 'system', 'notification'). This helps filter out irrelevant system-generated content unless explicitly relevant to the discussion.
- **`isActionItem`** (boolean, optional): Suggests whether the message explicitly or implicitly contains an actionable item. This allows priority extraction of tasks if pre-tagged.
- **`hasLinks`** (boolean, optional): Indicates if the message contains hyperlinks. This helps quickly identify messages with external references.
- **`links`** (list of strings, optional): A list of links extracted from the content of the message. Links are analyzed to understand their relevance to the conversation (e.g., GitHub pull requests, Jira tickets, external resources).
- **`reactions`** (list of strings, optional): A list of emoji reactions applied to the message. Reactions can signal agreement, approval, or acknowledgment of tasks or points raised.
- **`relatedResources`** (list of dictionaries, optional): Structured references to related external tools/resources (e.g., Jira, GitHub). Each dictionary may include fields like resource type, identifier, and URL. This helps bring external conversation context into the analysis.
- **`conversationTags`** (list of strings, optional): Pre-tagged indicators for portions of the conversation (e.g., 'problem_statement', 'decision_made', 'open_question'). This helps categorize the input and focus on critical parts.

**IMPORTANT - MUST ALWAYS BE FOLLOWED**:
- The input will always be in the above format - so please stick to the output format correctly. 
- Focus on important messages

Your output must follow this JSON format:

```json
{
    "summary": "A concise summary of the entire conversation, covering key points, significant observations, and the general context discussed.",
    "problemsDiscussed": [
        "A list of specific problems or challenges identified within the thread."
    ],
    "relevantLinks": [
        {
            "link": "The complete URL of the link mentioned.",
            "context": "A brief explanation of the link's relevance to the conversation."
        }
    ],
    "actionItems": [
        {
            "task": "Description of the action item.",
            "responsible": "Name or identifier of the individual/team responsible for the task (if inferred)."
        }
    ]
}
```

### Key Requirements
- Carefully extract and structure actionable insights from the input JSON object.
- Infer responsibility and intent where explicitly stated or reasonably implied.
- Provide a detailed description for each link extracted.
- Use chronological ordering and hierarchical threading (via `isReply` and `inReplyToMessageId`) to group sub-discussions within threads.

### Example Input
Here is what the JSON input might look like:

```json
[
    {
        "messageId": "m1",
        "timestamp": "2023-06-01T10:00:00Z",
        "sender": "alice",
        "content": "Hey team, we're seeing some timeout issues in the API.",
        "isReply": false,
        "inReplyToMessageId": null,
        "mentions": ["bob"],
        "threadId": "t1",
        "hasLinks": false,
        "isActionItem": false
    }
]
```

### Output Format
Analyze the input and provide a structured JSON response that includes:

- **summary**: A concise summary covering the general flow of the conversation.
- **problemsDiscussed**: A list of identified problems or blockers.
- **relevantLinks**: Extracted links with contextual explanations for each.
- **actionItems**: A list of pending tasks or decisions with responsibilities attached if identifiable.

Focus on producing accurate insights and usable responses suitable for tracking outcomes and decision-making."""
                },
                {
                    "role": "user", 
                    "content": f"Please summarize the following Slack conversation:\n\n{conversation_text}"
                }
            ]
        )

        
        
        return response.message.content
    
    def _format_conversation_for_llm(self, conversation: List[SlackMessage]) -> str:
        formatted_messages = []
        
        for message in conversation:
            timestamp_str = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            message_str = f"[{timestamp_str}] {message.sender}: {message.content}"
            
            if message.isReply and message.inReplyToMessageId:
                message_str += f" (Reply to message: {message.inReplyToMessageId})"
            
            if message.mentions:
                mentions_str = ", ".join(message.mentions)
                message_str += f" (Mentions: {mentions_str})"
            
            formatted_messages.append(message_str)
        
        return "\n".join(formatted_messages)


def generate_conversation_summary(conversation: List[SlackMessage]) -> str:
    """
    Convenience function to generate a conversation summary.
    
    Args:
        conversation (List[SlackMessage]): List of SlackMessage objects representing the conversation
        
    Returns:
        str: The generated summary content from the LLM response
    """
    generator = ConversationSummaryGenerator()
    return generator.generate_conversation_summary(conversation)
