/**
 * Lógica do Assistente de IA (Barista AI) em TypeScript
 */

class AIAssistant {
    private btn: HTMLElement | null;
    private window: HTMLElement | null;
    private messages: HTMLElement | null;
    private input: HTMLInputElement | null;
    private sendBtn: HTMLElement | null;
    private closeBtn: HTMLElement | null;

    constructor() {
        this.btn = document.getElementById('ai-btn');
        this.window = document.getElementById('ai-chat-window');
        this.messages = document.getElementById('ai-messages');
        this.input = document.getElementById('ai-input') as HTMLInputElement;
        this.sendBtn = document.getElementById('send-ai');
        this.closeBtn = document.getElementById('close-ai');

        this.init();
    }

    private init(): void {
        if (!this.btn || !this.window) return;

        this.btn.addEventListener('click', () => this.toggleChat());
        if (this.closeBtn) this.closeBtn.addEventListener('click', () => this.toggleChat());
        
        if (this.sendBtn) {
            this.sendBtn.addEventListener('click', () => this.sendMessage());
        }

        if (this.input) {
            this.input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.sendMessage();
            });
        }
    }

    private toggleChat(): void {
        if (this.window) {
            const isVisible = this.window.style.display === 'flex';
            this.window.style.display = isVisible ? 'none' : 'flex';
            if (!isVisible && this.input) {
                this.input.focus();
            }
        }
    }

    private async sendMessage(): Promise<void> {
        if (!this.input || !this.messages) return;

        const text = this.input.value.trim();
        if (!text) return;

        // Adicionar mensagem do utilizador
        this.addMessage(text, 'user');
        this.input.value = '';

        // Adicionar indicador de "a escrever..."
        const typingId = this.addMessage('O Barista AI está a pensar...', 'bot typing');

        try {
            const response = await fetch('/ai-chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();
            
            // Remover indicador de escrita
            const typingMsg = document.getElementById(typingId);
            if (typingMsg) typingMsg.remove();

            if (data.response) {
                this.addMessage(data.response, 'bot');
            } else {
                this.addMessage("Desculpa, tive um problema ao processar isso.", 'bot');
            }
        } catch (error) {
            console.error("Erro na IA:", error);
            const typingMsg = document.getElementById(typingId);
            if (typingMsg) typingMsg.remove();
            this.addMessage("Erro de ligação ao servidor.", 'bot');
        }
    }

    private addMessage(text: string, type: string): string {
        if (!this.messages) return '';

        // Garantir ID único mesmo se as mensagens forem criadas no mesmo milissegundo
        const id = 'msg-' + Date.now() + '-' + Math.floor(Math.random() * 10000);
        const msgDiv = document.createElement('div');
        msgDiv.id = id;
        msgDiv.className = `ai-msg ${type}`;
        msgDiv.innerText = text;
        this.messages.appendChild(msgDiv);
        
        // Scroll para baixo
        this.messages.scrollTop = this.messages.scrollHeight;
        
        return id;
    }

    private getCsrfToken(): string {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    new AIAssistant();
});
