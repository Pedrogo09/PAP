/**
 * Lógica da Página de Checkout (TypeScript)
 * Valida horários e métodos de pagamento
 */

interface Schedule {
    is_open: boolean;
    opening_time: string;
    closing_time: string;
}

interface Schedules {
    [key: number]: Schedule;
}

class CheckoutManager {
    private schedules: Schedules;
    private dayNames: string[];
    private dateInput: HTMLInputElement | null;
    private hourSelect: HTMLSelectElement | null;
    private minuteSelect: HTMLSelectElement | null;
    private dateWarning: HTMLElement | null;
    private timeWarning: HTMLElement | null;
    private timeHiddenInput: HTMLInputElement | null;
    private paymentMethodSelect: HTMLSelectElement | null;
    private paymentInfo: HTMLElement | null;
    private multibancoInfo: HTMLElement | null;
    private checkoutForm: HTMLFormElement | null;
    private confirmCheckbox: HTMLInputElement | null;

    constructor() {
        // Obter dados dos horários do Django via variável global
        try {
            this.schedules = (window as any).SCHEDULES_DATA || [];
            console.log('Schedules loaded:', this.schedules);
        } catch (e) {
            console.error('Erro ao obter schedules:', e);
            this.schedules = [];
        }
        this.dayNames = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo'];

        // Obter elementos do DOM
        this.dateInput = document.getElementById('scheduled_date') as HTMLInputElement;
        this.hourSelect = document.getElementById('scheduled_hour') as HTMLSelectElement;
        this.minuteSelect = document.getElementById('scheduled_minute') as HTMLSelectElement;
        this.dateWarning = document.getElementById('dateWarning');
        this.timeWarning = document.getElementById('timeWarning');
        this.timeHiddenInput = document.getElementById('scheduled_time') as HTMLInputElement;
        this.paymentMethodSelect = document.getElementById('payment_method') as HTMLSelectElement;
        this.paymentInfo = document.getElementById('paymentInfo');
        this.multibancoInfo = document.getElementById('multibanco_info');
        this.checkoutForm = document.getElementById('checkoutForm') as HTMLFormElement;
        this.confirmCheckbox = document.getElementById('confirm_atm') as HTMLInputElement;

        this.init();
    }

    private init(): void {
        if (!this.hourSelect || !this.minuteSelect) return;

        this.populateTimeSelects();
        this.setupEventListeners();
    }

    private populateTimeSelects(): void {
        if (!this.hourSelect || !this.minuteSelect) return;

        // Limpar opções existentes
        this.hourSelect.innerHTML = '<option value="">Selecione a hora...</option>';
        this.minuteSelect.innerHTML = '<option value="">Selecione o minuto...</option>';

        // Adicionar horas (0-23)
        for (let h = 0; h < 24; h++) {
            const option = document.createElement('option');
            option.value = String(h).padStart(2, '0');
            option.textContent = String(h).padStart(2, '0');
            this.hourSelect.appendChild(option);
        }

        // Adicionar minutos (0-59)
        for (let m = 0; m < 60; m++) {
            const option = document.createElement('option');
            option.value = String(m).padStart(2, '0');
            option.textContent = String(m).padStart(2, '0');
            this.minuteSelect.appendChild(option);
        }
    }

    private setupEventListeners(): void {
        if (this.dateInput) {
            this.dateInput.addEventListener('change', () => this.validateDateTime());
        }
        if (this.hourSelect) {
            this.hourSelect.addEventListener('change', () => this.validateDateTime());
        }
        if (this.minuteSelect) {
            this.minuteSelect.addEventListener('change', () => this.validateDateTime());
        }
        if (this.paymentMethodSelect) {
            this.paymentMethodSelect.addEventListener('change', () => this.updatePaymentInfo());
        }
        if (this.checkoutForm) {
            this.checkoutForm.addEventListener('submit', (e) => this.validateForm(e));
        }
    }

    private validateDateTime(): void {
        if (!this.dateInput || !this.hourSelect || !this.minuteSelect || !this.dateWarning || !this.timeWarning || !this.timeHiddenInput) return;

        const dateInput = this.dateInput.value;
        const hour = this.hourSelect.value;
        const minute = this.minuteSelect.value;

        if (!dateInput) {
            this.dateWarning.classList.add('d-none');
            this.timeWarning.classList.add('d-none');
            return;
        }

        // Obter dia da semana (0=segunda, 6=domingo)
        const date = new Date(dateInput);
        const dayOfWeek = (date.getDay() + 6) % 7; // Converter de JS (0=domingo) para Django (0=segunda)

        const schedule = this.schedules[dayOfWeek];

        // Verificar se o dia está aberto
        if (!schedule || !schedule.is_open) {
            this.dateWarning.classList.remove('d-none');
            this.timeWarning.classList.add('d-none');
            this.timeHiddenInput.value = '';
            return;
        } else {
            this.dateWarning.classList.add('d-none');
        }

        // Verificar hora se preenchida
        if (hour && minute) {
            const time = `${hour}:${minute}`;
            const openTime = schedule.opening_time;
            const closeTime = schedule.closing_time;

            if (time >= openTime && time <= closeTime) {
                this.timeWarning.classList.add('d-none');
                this.timeHiddenInput.value = time;
            } else {
                this.timeWarning.classList.remove('d-none');
                const availableHoursElement = document.getElementById('availableHours');
                if (availableHoursElement) {
                    availableHoursElement.textContent = `${openTime} às ${closeTime}`;
                }
                this.timeHiddenInput.value = '';
            }
        } else {
            this.timeWarning.classList.add('d-none');
            this.timeHiddenInput.value = '';
        }
    }

    private updatePaymentInfo(): void {
        if (!this.paymentMethodSelect || !this.paymentInfo || !this.multibancoInfo) return;

        const method = this.paymentMethodSelect.value;

        if (method === 'card') {
            this.paymentInfo.textContent = 'Débito direto do seu saldo do cartão escolar';
            this.multibancoInfo.classList.add('d-none');
        } else {
            this.paymentInfo.textContent = 'Receberá referência Multibanco para pagamento';
            this.multibancoInfo.classList.remove('d-none');
        }
    }

    private validateForm(e: Event): void {
        if (!this.dateInput || !this.hourSelect || !this.minuteSelect || !this.paymentMethodSelect || !this.confirmCheckbox || !this.dateWarning || !this.timeWarning) return;

        // Obter valores diretamente do DOM em vez de meta tags
        const balanceElement = document.querySelector('[data-balance]');
        const totalElement = document.querySelector('[data-total]');
        
        const balance = balanceElement ? parseFloat(balanceElement.getAttribute('data-balance') || '0') : 0;
        const total = totalElement ? parseFloat(totalElement.getAttribute('data-total') || '0') : 0;
        
        const method = this.paymentMethodSelect.value;
        const dateInput = this.dateInput.value;
        const hour = this.hourSelect.value;
        const minute = this.minuteSelect.value;

        // Validar se a data foi preenchida
        if (!dateInput) {
            e.preventDefault();
            alert('Por favor, selecione a data de levantamento.');
            this.dateInput.focus();
            return;
        }

        // Validar se o dia está aberto
        if (!this.dateWarning.classList.contains('d-none')) {
            e.preventDefault();
            alert('O bar está fechado neste dia. Por favor, escolha outro dia.');
            return;
        }

        // Validar se a hora e minuto foram preenchidos
        if (!hour) {
            e.preventDefault();
            alert('Por favor, selecione a hora de levantamento.');
            this.hourSelect.focus();
            return;
        }

        if (!minute) {
            e.preventDefault();
            alert('Por favor, selecione o minuto de levantamento.');
            this.minuteSelect.focus();
            return;
        }

        // Validar se a hora está disponível
        if (!this.timeWarning.classList.contains('d-none')) {
            e.preventDefault();
            const availableTextElement = document.getElementById('availableHours');
            const availableText = availableTextElement ? availableTextElement.textContent : '';
            alert(`Este horário não está disponível. ${availableText}`);
            return;
        }

        // Validar método de pagamento
        if (method === 'card') {
            if (balance < total) {
                e.preventDefault();
                alert(`Saldo insuficiente! Saldo: €${balance.toFixed(2)}, Total: €${total.toFixed(2)}`);
                return;
            }
        } else if (method === 'atm') {
            if (!this.confirmCheckbox.checked) {
                e.preventDefault();
                alert('Por favor, confirme que vai pagar por Multibanco.');
                this.confirmCheckbox.focus();
                return;
            }
        }
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    new CheckoutManager();
});
