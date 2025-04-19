// ReactFrontend/lib/chatPermissions.ts

// Types for pending button components
export interface PendingComponent {
    name: string;
    disableMessage: string;
  }
  
  // Public API for managing chat permissions
  declare global {
    interface Window {
      chatPermissions: ChatPermissionManager;
      uploadRequiresCompletion?: boolean;
      sendMessage?: (...args: any[]) => any;
    }
  }
  
  export interface ChatPermissionManager {
    disableChat: (reason?: string) => void;
    enableChat: () => void;
    registerButtonComponent: (componentName: string, options?: { disableMessage?: string }) => void;
    markButtonSelected: (componentName: string) => void;
    handleUploadButtonClick: () => void;
    isChatEnabled: () => boolean;
  }
  
  export function createChatPermissionManager(): ChatPermissionManager {
    console.log('Initializing Chat Permission Manager...');
  
    let chatEnabled = true;
    let disabledReason = '';
    let pendingButtonSelections: PendingComponent[] = [];
  
    const chatInput = document.getElementById('chat-input') as HTMLInputElement | null;
    const sendButton = document.getElementById('send-button') as HTMLButtonElement | null;
  
    const setupUI = () => {
      const styleElement = document.createElement('style');
      styleElement.textContent = `
        #send-button.chat-disabled { opacity: 0.5; cursor: not-allowed; }
        #chat-input.chat-disabled { opacity: 0.7; background-color: rgba(200,200,200,0.1); cursor: not-allowed; pointer-events: none; }
        .chat-input-tooltip { position: fixed; background-color: rgba(0,0,0,0.7); color: #fff; padding: 6px 10px; border-radius: 4px; font-size: 12px; pointer-events: none; z-index: 1000; opacity: 0; transition: opacity 0.15s ease; transform: translate(10px,-25px); }
      `;
      document.head.appendChild(styleElement);
    };
  
    let tooltipEl: HTMLDivElement | null = null;
    const setupTooltip = () => {
      tooltipEl = document.createElement('div');
      tooltipEl.className = 'chat-input-tooltip';
      tooltipEl.textContent = 'Please select one of the options above';
      document.body.appendChild(tooltipEl);
  
      chatInput?.addEventListener('mousemove', (e) => {
        if (!chatEnabled && tooltipEl) {
          tooltipEl.style.left = `${e.clientX}px`;
          tooltipEl.style.top = `${e.clientY}px`;
          tooltipEl.style.opacity = '1';
        }
      });
      chatInput?.addEventListener('mouseleave', () => {
        if (tooltipEl) tooltipEl.style.opacity = '0';
      });
    };
  
    const updateUI = () => {
      if (!chatInput || !sendButton) return;
      if (!chatEnabled) {
        sendButton.classList.add('chat-disabled');
        chatInput.classList.add('chat-disabled');
        chatInput.disabled = true;
      } else {
        sendButton.classList.remove('chat-disabled');
        chatInput.classList.remove('chat-disabled');
        chatInput.disabled = false;
        if (tooltipEl) tooltipEl.style.opacity = '0';
      }
    };
  
    const disableChat = (reason = 'Please select an option to continue'): void => {
      chatEnabled = false;
      disabledReason = reason;
      updateUI();
    };
  
    const enableChat = (): void => {
      chatEnabled = true;
      disabledReason = '';
      updateUI();
    };
  
    const overrideSendMessage = (): void => {
      const originalSend = window.sendMessage;
      window.sendMessage = (...args) => {
        if (!chatEnabled) {
          console.log('Chat disabled:', disabledReason);
          if (sendButton) {
            const origColor = sendButton.style.backgroundColor;
            sendButton.style.backgroundColor = 'rgba(255,59,48,0.3)';
            setTimeout(() => {
              sendButton.style.backgroundColor = origColor;
            }, 300);
          }
          return false;
        }
        return originalSend?.(...args);
      };
  
      if (sendButton) {
        const newBtn = sendButton.cloneNode(true) as HTMLButtonElement;
        sendButton.parentNode?.replaceChild(newBtn, sendButton);
        newBtn.addEventListener('click', (e) => {
          if (!chatEnabled) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Chat send blocked:', disabledReason);
          } else {
            window.sendMessage?.();
          }
        });
      }
    };
  
    const registerButtonComponent = (componentName: string, options: { disableMessage?: string } = {}): void => {
      pendingButtonSelections.push({ name: componentName, disableMessage: options.disableMessage || `Please select an option for ${componentName}` });
      if (pendingButtonSelections.length === 1) {
        disableChat(pendingButtonSelections[0].disableMessage);
      }
    };
  
    const markButtonSelected = (componentName: string): void => {
      pendingButtonSelections = pendingButtonSelections.filter(c => c.name !== componentName);
      if (pendingButtonSelections.length === 0) {
        enableChat();
      } else {
        disableChat(pendingButtonSelections[0].disableMessage);
      }
    };
  
    const handleUploadButtonClick = (): void => {
      window.uploadRequiresCompletion = true;
      const imageUpload = document.getElementById('image-upload') as HTMLInputElement | null;
      const originalOnChange = imageUpload?.onchange;
      if (imageUpload) {
        imageUpload.onchange = function (e: Event & { target: HTMLInputElement }) {
          if (e.target.files?.length) {
            window.uploadRequiresCompletion = false;
            window.chatPermissions.markButtonSelected('productSelection');
          }
          originalOnChange?.apply(this, arguments as any);
          setTimeout(() => {
            imageUpload.onchange = originalOnChange;
          }, 100);
        };
      }
    };
  
    const init = (): void => {
      setupUI();
      setupTooltip();
      overrideSendMessage();
      enableChat();
      chatInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey && !chatEnabled) {
          e.preventDefault();
          console.log('Enter blocked:', disabledReason);
        }
      }, true);
    };
  
    init();
  
    return { disableChat, enableChat, registerButtonComponent, markButtonSelected, handleUploadButtonClick, isChatEnabled: () => chatEnabled };
  }
  
  export const chatPermissions = createChatPermissionManager();
  console.log('Chat Permission Manager initialized');
  
  export {};
  