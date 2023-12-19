document.addEventListener('DOMContentLoaded', function () {
    var $navbarLoad = Array.prototype.slice.call(document.querySelectorAll('.navbar-burger'), 0);
    if ($navbarLoad.length > 0) {
        $navbarLoad.forEach(function ($click) {
            $click.addEventListener('click', function () {

                var target = $click.dataset.target;
                var $target = document.getElementById(target);

                $click.classList.toggle('is-active');
                $target.classList.toggle('is-active');

            });
        });
    }

});

function toggleModal(modalId) {
    var modal = document.getElementById(modalId);
    modal.classList.toggle('is-active');
}
function incrementQuantity(productId) {
    var quantityInput = document.getElementById('jumlah_pesanan_' + productId);
    quantityInput.value = parseInt(quantityInput.value) + 1;
}

function decrementQuantity(productId) {
    var quantityInput = document.getElementById('jumlah_pesanan_' + productId);
    var newValue = parseInt(quantityInput.value) - 1;
    if (newValue >= 1) {
        quantityInput.value = newValue;
    }
}

function incrementCart(productId) {
    var quantityInput = document.getElementById('insert_cart_' + productId);
    quantityInput.value = parseInt(quantityInput.value) + 1;
}

function decrementCart(productId) {
    var quantityInput = document.getElementById('insert_cart_' + productId);
    var newValue = parseInt(quantityInput.value) - 1;
    if (newValue >= 1) {
        quantityInput.value = newValue;
    }
}

function filterProducts(category) {
    document.querySelectorAll('.product-card').forEach(card => {
        card.style.display = 'none';
    });

    if (category === 'All') {
        document.querySelectorAll('.product-card').forEach(card => {
            card.style.display = 'block';
        });
    } else {
        document.querySelectorAll(`.product-card[data-category="${category}"]`).forEach(card => {
            card.style.display = 'block';
        });
    }
}

function searchProducts() {
    const searchInput = document.getElementById('searchInput').value.toLowerCase();

    document.querySelectorAll('.product-card').forEach(card => {
        card.style.display = 'none';
    });

    document.querySelectorAll('.product-card').forEach(card => {
        const productName = card.querySelector('.subtitle').innerText.toLowerCase();
        if (productName.includes(searchInput)) {
            card.style.display = 'block';
        }
    });
}