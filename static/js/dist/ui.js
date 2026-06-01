/**
 * Utilitários de UI para o Bar Escolar - Compilado de TypeScript
 */
export class UIManager {
    static initToasts() {
        document.addEventListener('DOMContentLoaded', () => {
            const toasts = document.querySelectorAll('.alert');
            toasts.forEach((toastElement) => {
                const toast = toastElement;
                // Só esconde automaticamente mensagens de sucesso ou cart-toast
                if (toast.classList.contains('alert-success')) {
                    this.hideWithAnimation(toast, 4000);
                }
            });
        });
    }
    static hideWithAnimation(element, delay) {
        setTimeout(() => {
            element.classList.add('toast-hide');
            // Espera a animação de CSS terminar (0.5s definida no base.html)
            setTimeout(() => {
                // @ts-ignore - bootstrap is global from CDN
                const bsAlert = bootstrap.Alert.getOrCreateInstance(element);
                if (bsAlert) {
                    bsAlert.close();
                }
            }, 500);
        }, delay);
    }
    static setupAutoRefresh(intervalMs = 30000) {
        console.log(`Auto-refresh configurado para ${intervalMs}ms`);
        setTimeout(() => {
            // Apenas atualiza se não houver inputs focados para não estragar a experiência do utilizador
            const activeElement = document.activeElement;
            const isInput = activeElement instanceof HTMLInputElement ||
                activeElement instanceof HTMLTextAreaElement;
            if (!isInput) {
                location.reload();
            }
            else {
                // Se estiver a escrever, tenta novamente daqui a 10 segundos
                this.setupAutoRefresh(10000);
            }
        }, intervalMs);
    }
}
// Inicializar componentes
UIManager.initToasts();
