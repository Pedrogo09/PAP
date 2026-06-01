/**
 * Lógica do Assistente de IA (Barista AI) - Compilado de TypeScript
 */
class AIAssistant {
    constructor() {
        this.btn = document.getElementById('ai-btn');
        this.window = document.getElementById('ai-chat-window');
        this.messages = document.getElementById('ai-messages');
        this.input = document.getElementById('ai-input');
        this.sendBtn = document.getElementById('send-ai');
        this.closeBtn = document.getElementById('close-ai');
        this.init();
    }
    init() {
        if (!this.btn || !this.window)
            return;
        this.btn.addEventListener('click', () => this.toggleChat());
        if (this.closeBtn)
            this.closeBtn.addEventListener('click', () => this.toggleChat());
        if (this.sendBtn) {
            this.sendBtn.addEventListener('click', () => this.sendMessage());
        }
        if (this.input) {
            this.input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter')
                    this.sendMessage();
            });
        }
    }
    toggleChat() {
        if (this.window) {
            const isVisible = this.window.style.display === 'flex';
            this.window.style.display = isVisible ? 'none' : 'flex';
            if (!isVisible && this.input) {
                this.input.focus();
            }
        }
    }
    async sendMessage() {
        if (!this.input || !this.messages)
            return;
        const text = this.input.value.trim();
        if (!text)
            return;
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
            if (typingMsg)
                typingMsg.remove();
            if (data.response) {
                this.addMessage(data.response, 'bot');
            }
            else {
                this.addMessage("Desculpa, tive um problema ao processar isso.", 'bot');
            }
            // Atualizar o badge do carrinho se necessário
            if (data.cart_total !== undefined) {
                this.updateCartBadge(data.cart_total);
            }
        }
        catch (error) {
            console.error("Erro na IA:", error);
            const typingMsg = document.getElementById(typingId);
            if (typingMsg)
                typingMsg.remove();
            this.addMessage("Erro de ligação ao servidor.", 'bot');
        }
    }
    addMessage(text, type) {
        if (!this.messages)
            return '';
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
    getCsrfToken() {
        var _a;
        const cookieValue = (_a = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))) === null || _a === void 0 ? void 0 : _a.split('=')[1];
        return cookieValue || '';
    }
    updateCartBadge(totalItems) {
        const cartIcon = document.querySelector('.fa-shopping-cart');
        if (cartIcon) {
            const cartLink = cartIcon.closest('a');
            if (cartLink) {
                let badge = cartLink.querySelector('.badge-cart');
                if (totalItems > 0) {
                    if (!badge) {
                        badge = document.createElement('span');
                        badge.className = 'badge-cart';
                        cartLink.appendChild(badge);
                    }
                    badge.textContent = totalItems.toString();
                } else if (badge) {
                    badge.remove();
                }
            }
        }
    }
}
// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    new AIAssistant();
});
