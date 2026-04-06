'use client';

import ChatComponent, { ChatConfig, UiConfig } from "@/components/ui/chat-interface";

export default function DemoOne() {
  const uiConfig: UiConfig = {
    containerWidth: 520,
    containerHeight: 430,
    backgroundColor: '#FFFFFF',
    autoRestart: true,
    restartDelay: 3600,
    loader: {
      dotColor: '#8B78FF'
    },
    linkBubbles: {
      backgroundColor: '#F3EEFF',
      textColor: '#5B4BC4',
      iconColor: '#5B4BC4',
      borderColor: '#E2D9FF'
    },
    leftChat: {
      backgroundColor: '#FFFFFF',
      textColor: '#1B2037',
      borderColor: '#E8EAFB',
      showBorder: true,
      nameColor: '#6974B8'
    },
    rightChat: {
      backgroundColor: '#EEF0FF',
      textColor: '#1B2037',
      borderColor: '#EEF0FF',
      showBorder: false,
      nameColor: '#A06CCB'
    }
  };

  const chatConfig: ChatConfig = {
    leftPerson: {
      name: "Serenity AI",
      avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=200&q=80"
    },
    rightPerson: {
      name: "Anna",
      avatar: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?auto=format&fit=crop&w=200&q=80"
    },
    messages: [
      {
        id: 1,
        sender: 'right',
        type: 'text',
        content: 'I am feeling overwhelmed again and my chest has been tight since this morning.',
        loader: {
          enabled: true,
          delay: 400,
          duration: 950
        }
      },
      {
        id: 2,
        sender: 'left',
        type: 'text',
        content: 'I am here with you. I am marking this as an elevated anxiety check-in and keeping the counselor queue warm.',
        loader: {
          enabled: true,
          delay: 250,
          duration: 1200
        }
      },
      {
        id: 3,
        sender: 'left',
        type: 'text-with-links',
        content: 'While we wait, these supports are already active for this conversation.',
        maxWidth: 'max-w-md',
        links: [
          { text: 'Breathing Coach' },
          { text: 'Priority Routing' },
          { text: 'Session Notes' }
        ],
        loader: {
          enabled: true,
          delay: 300,
          duration: 900
        }
      },
      {
        id: 4,
        sender: 'right',
        type: 'image',
        content: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=700&q=80',
        loader: {
          enabled: true,
          delay: 300,
          duration: 1200
        }
      },
      {
        id: 5,
        sender: 'left',
        type: 'text',
        content: 'Counselor note draft is ready. Risk remains moderate and stable, with no immediate self-harm indicators in the last turn.',
        loader: {
          enabled: true,
          delay: 300,
          duration: 1000
        }
      }
    ]
  };

  return <ChatComponent config={chatConfig} uiConfig={uiConfig} />;
}
