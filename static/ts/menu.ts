/**
 * Lógica da Página de Menu (TypeScript)
 * Gerencia filtros, carrinho e favoritos
 */

class MenuManager {
    private filterForm: HTMLFormElement | null;
    private productsGrid: HTMLElement | null;
    private searchInput: HTMLInputElement | null;
    private searchTimeout: number | null;

    constructor() {
        this.filterForm = document.getElementById('filterForm') as HTMLFormElement;
        this.productsGrid = document.getElementById('productsGrid');
        this.searchInput = document.getElementById('realTimeSearch') as HTMLInputElement;
        this.searchTimeout = null;

        this.init();
    }

    private init(): void {
        if (!this.filterForm || !this.productsGrid || !this.searchInput) return;

        // Listen for Form Changes (Pills)
        this.filterForm.querySelectorAll('input').forEach(input => {
            input.addEventListener('change', () => this.updateResults());
        });

        // Real-time Search with Debounce
        this.searchInput.addEventListener('input', () => {
            if (this.searchTimeout) clearTimeout(this.searchTimeout);
            this.searchTimeout = window.setTimeout(() => this.updateResults(), 300);
        });

        // Highlight selected pills visually, handle scroll centering + scroll to grid
        this.filterForm.addEventListener('change', (e) => this.handleFormChange(e));

        // Initial Bind
        this.initDynamicEvents();
    }

    private handleFormChange(e: Event): void {
        const target = e.target as HTMLInputElement;
        
        if (target.name === 'sort' || target.name === 'price') {
            const group = target.closest('.btn-group');
            if (group) {
                group.querySelectorAll('label').forEach(lbl => {
                    lbl.classList.remove('bg-white', 'shadow-sm', 'text-primary');
                });
                const label = group.querySelector(`label[for="${target.id}"]`);
                if (label) {
                    label.classList.add('bg-white', 'shadow-sm', 'text-primary');
                }
            }
        }

        if (target.name === 'category' && this.filterForm) {
            // Centrar o cartão selecionado no scroll horizontal
            const activeLabel = this.filterForm.querySelector(`label[for="${target.id}"]`);
            if (activeLabel) {
                activeLabel.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
            }
            
            // Scroll suave até à grelha de produtos
            const targetScroll = document.getElementById('productsGrid');
            if (targetScroll) {
                setTimeout(() => {
                    targetScroll.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }, 150);
            }
        }
    }

    private updateResults(): void {
        if (!this.filterForm || !this.productsGrid) return;

        const formData = new FormData(this.filterForm);
        const params = new URLSearchParams(formData as any);
        
        // Mostrar/ocultar secção de sugestões dinamicamente
        const categoryVal = formData.get('category');
        const searchVal = formData.get('search');
        const favoritesVal = formData.get('favorites');
        const suggestionsSection = document.getElementById('suggestionsSection');
        
        if (suggestionsSection) {
            if (!categoryVal && !searchVal && !favoritesVal) {
                suggestionsSection.style.display = 'block';
            } else {
                suggestionsSection.style.display = 'none';
            }
        }
        
        // Show loading state
        this.productsGrid.style.opacity = '0.5';
        this.productsGrid.style.transition = 'opacity 0.2s';

        fetch(`${window.location.pathname}?${params.toString()}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.text())
        .then(html => {
            if (this.productsGrid) {
                this.productsGrid.innerHTML = html;
                this.productsGrid.style.opacity = '1';
            }
            
            // Update URL without reload (optional but good for UX)
            const newUrl = `${window.location.pathname}?${params.toString()}`;
            window.history.pushState({path: newUrl}, '', newUrl);

            // Re-bind dynamic events (Cart and Favorites)
            this.initDynamicEvents();
        })
        .catch(err => {
            console.error('Erro ao filtrar produtos:', err);
            if (this.productsGrid) {
                this.productsGrid.style.opacity = '1';
            }
        });
    }

    private initDynamicEvents(): void {
        // Cart Buttons
        document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
            (btn as HTMLElement).addEventListener('click', (e: Event) => {
                e.preventDefault();
                this.handleAddToCart(btn as HTMLElement);
            });
        });

        // Favorite Buttons
        document.querySelectorAll('.favorite-btn').forEach(btn => {
            (btn as HTMLElement).addEventListener('click', (e: Event) => {
                e.preventDefault();
                this.toggleFavorite(btn as HTMLElement);
            });
        });
    }

    private handleAddToCart(btn: HTMLElement): void {
        const productId = btn.getAttribute('data-product-id');
        if (!productId) return;

        const originalContent = btn.innerHTML;
        const cartBadge = document.querySelector('.badge-cart');
        const cartLink = document.querySelector('a[href*="/cart/"]');

        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        (btn as HTMLButtonElement).disabled = true;

        fetch(`/cart/add/${productId}/`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (cartBadge) {
                    cartBadge.textContent = data.cart_count;
                } else if (cartLink) {
                    const newBadge = document.createElement('span');
                    newBadge.className = 'badge-cart';
                    newBadge.textContent = data.cart_count;
                    cartLink.appendChild(newBadge);
                }
                this.showCartToast(data.product_name, data.total_items, data.total_price);
            }
        })
        .finally(() => {
            btn.innerHTML = originalContent;
            (btn as HTMLButtonElement).disabled = false;
        });
    }

    private toggleFavorite(btn: HTMLElement): void {
        const productId = btn.getAttribute('data-product-id');
        if (!productId) return;

        const icon = btn.querySelector('i');
        if (!icon) return;

        fetch(`/product/${productId}/favorite/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.is_favorite) {
                        icon.classList.replace('far', 'fas');
                    } else {
                        icon.classList.replace('fas', 'far');
                        // If we are currently in "Only Favorites" view, hide the card
                        const urlParams = new URLSearchParams(window.location.search);
                        if (urlParams.get('favorites') === 'true') {
                            const card = btn.closest('.product-card-container');
                            if (card) card.remove();
                        }
                    }
                }
            });
    }

    private showCartToast(name: string, items: number, price: string): void {
        const container = document.querySelector('div[style*="fixed"]');
        const toastHtml = `
            <div class="alert alert-success cart-toast alert-dismissible fade show" role="alert" 
                 style="background: #1e1e1e; color: #fff; border: 1px solid rgba(255,165,0,0.3); margin-bottom: 0;">
                <i class="fas fa-check-circle text-success me-2"></i>
                <div class="d-flex justify-content-between align-items-center" style="min-width: 250px;">
                    <div>
                        <strong>${name}</strong> adicionado.<br>
                        <small class="text-muted">${items} item(s) • Total: €${price}</small>
                    </div>
                    <a href="/cart/" class="btn btn-sm btn-primary ms-3">Ver Carrinho</a>
                </div>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert"></button>
                <div class="toast-progress"></div>
            </div>
        `;
        const toastElement = document.createElement('div');
        toastElement.innerHTML = toastHtml;
        const newToast = toastElement.firstElementChild as HTMLElement;
        
        if (container) {
            container.appendChild(newToast);
        } else {
            const newContainer = document.createElement('div');
            newContainer.style = "position: fixed; bottom: 20px; right: 20px; z-index: 1050; display: flex; flex-direction: column; gap: 10px;";
            newContainer.appendChild(newToast);
            document.body.appendChild(newContainer);
        }

        setTimeout(() => {
            newToast.classList.add('toast-hide');
            setTimeout(() => { newToast.remove(); }, 500);
        }, 4000);
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    new MenuManager();
});
