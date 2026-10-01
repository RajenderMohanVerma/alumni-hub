// ===== ADVANCED ANIMATION UTILITIES =====

// Scroll-Triggered Animation Observer
class ScrollAnimator {
    constructor() {
        this.observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -100px 0px'
        };
        this.init();
    }

    init() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animated');
                    // For counter animations
                    if (entry.target.classList.contains('counter')) {
                        this.animateCounter(entry.target);
                    }
                }
            });
        }, this.observerOptions);

        // Observe all elements with scroll animation classes
        document.querySelectorAll('.scroll-fade-up, .scroll-fade-down, .scroll-fade-left, .scroll-fade-right, .scroll-scale-in, .scroll-rotate-in, .counter').forEach(el => {
            observer.observe(el);
        });
    }

    animateCounter(element) {
        const target = parseInt(element.getAttribute('data-target'));
        const duration = 2000;
        const increment = target / (duration / 16);
        let current = 0;

        const updateCounter = () => {
            current += increment;
            if (current < target) {
                element.textContent = Math.floor(current);
                requestAnimationFrame(updateCounter);
            } else {
                element.textContent = target;
            }
        };

        updateCounter();
    }
}

// Typing Effect
class TypingEffect {
    constructor(element, options = {}) {
        this.element = element;
        this.text = element.textContent;
        this.speed = options.speed || 100;
        this.delay = options.delay || 0;
        this.cursor = options.cursor !== false;
        this.init();
    }

    init() {
        this.element.textContent = '';
        if (this.cursor) {
            this.element.style.borderRight = '3px solid';
            this.element.style.animation = 'blink 0.75s step-end infinite';
        }

        setTimeout(() => {
            this.type(0);
        }, this.delay);
    }

    type(index) {
        if (index < this.text.length) {
            this.element.textContent += this.text.charAt(index);
            setTimeout(() => this.type(index + 1), this.speed);
        } else if (this.cursor) {
            setTimeout(() => {
                this.element.style.borderRight = 'none';
            }, 500);
        }
    }
}

// Magnetic Button Effect
class MagneticButton {
    constructor(element) {
        this.element = element;
        this.strength = 20;
        this.init();
    }

    init() {
        this.element.addEventListener('mousemove', (e) => {
            const rect = this.element.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;

            this.element.style.transform = `translate(${x / this.strength}px, ${y / this.strength}px)`;
        });

        this.element.addEventListener('mouseleave', () => {
            this.element.style.transform = 'translate(0, 0)';
        });
    }
}

// Ripple Effect
class RippleEffect {
    constructor(element) {
        this.element = element;
        this.init();
    }

    init() {
        this.element.addEventListener('click', (e) => {
            const ripple = document.createElement('span');
            ripple.classList.add('ripple');

            const rect = this.element.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';

            this.element.appendChild(ripple);

            setTimeout(() => ripple.remove(), 600);
        });
    }
}

// Parallax Effect
class ParallaxEffect {
    constructor(elements, speed = 0.5) {
        this.elements = elements;
        this.speed = speed;
        this.init();
    }

    init() {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            this.elements.forEach(el => {
                const speed = el.getAttribute('data-speed') || this.speed;
                el.style.transform = `translateY(${scrolled * speed}px)`;
            });
        });
    }
}

// Initialize all animations on DOM load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize scroll animations
    new ScrollAnimator();

    // Initialize typing effects
    document.querySelectorAll('.typing-effect').forEach(el => {
        new TypingEffect(el, {
            speed: parseInt(el.getAttribute('data-speed')) || 100,
            delay: parseInt(el.getAttribute('data-delay')) || 0
        });
    });

    // Initialize magnetic buttons
    document.querySelectorAll('.magnetic-btn').forEach(el => {
        new MagneticButton(el);
    });

    // Initialize ripple effects
    document.querySelectorAll('.ripple-btn').forEach(el => {
        new RippleEffect(el);
    });

    // Initialize parallax
    const parallaxElements = document.querySelectorAll('.parallax');
    if (parallaxElements.length > 0) {
        new ParallaxEffect(parallaxElements);
    }
});
