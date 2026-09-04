/**
 * Lógica da Página de Perfil (JavaScript compilado do TypeScript)
 * Gera QR code para identificação do utilizador
 */

class ProfileManager {
    constructor() {
        this.qrcodeElement = document.getElementById('qrcode');
        // O username é injetado pelo Django no template
        const usernameElement = document.querySelector('meta[name="username"]');
        this.username = usernameElement ? usernameElement.getAttribute('content') || '' : '';

        this.init();
    }

    init() {
        if (!this.qrcodeElement || !this.username) return;

        // Carregar a biblioteca QRCode dinamicamente
        this.loadQRCodeLibrary().then(() => {
            this.generateQRCode();
        }).catch(err => {
            console.error('Erro ao carregar biblioteca QRCode:', err);
        });
    }

    loadQRCodeLibrary() {
        return new Promise((resolve, reject) => {
            // Verificar se a biblioteca já está carregada
            if (typeof window.QRCode !== 'undefined') {
                resolve();
                return;
            }

            // Carregar a biblioteca QRCode
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js';
            script.onload = () => resolve();
            script.onerror = () => reject(new Error('Falha ao carregar biblioteca QRCode'));
            document.head.appendChild(script);
        });
    }

    generateQRCode() {
        if (!this.qrcodeElement || !this.username) return;

        try {
            new window.QRCode(this.qrcodeElement, {
                text: this.username,
                width: 128,
                height: 128,
                colorDark: "#000000",
                colorLight: "#ffffff",
                correctLevel: window.QRCode.CorrectLevel.H
            });
        } catch (error) {
            console.error('Erro ao gerar QR code:', error);
            if (this.qrcodeElement) {
                this.qrcodeElement.innerHTML = '<p class="text-danger">Erro ao gerar QR code</p>';
            }
        }
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    new ProfileManager();
});
