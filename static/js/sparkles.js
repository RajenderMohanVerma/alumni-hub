/**
 * Global High-Performance Particle System (Sparkles)
 * Optimized for high-refresh-rate displays (120Hz/144Hz+)
 */
class SparkleSystem {
    constructor() {
        this.canvas = document.getElementById('particle-canvas');
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d', { alpha: true });
        this.particles = [];
        this.mouseX = 0;
        this.mouseY = 0;
        this.isMoving = false;
        
        this.init();
    }

    init() {
        this.resize();
        window.addEventListener('resize', () => this.resize());
        
        window.addEventListener('mousemove', (e) => {
            this.mouseX = e.clientX;
            this.mouseY = e.clientY;
            this.isMoving = true;
            
            // Reduced spawn rate significantly on move to save CPU
            if (this.particles.length < 50 && Math.random() > 0.9) {
                this.createParticle(this.mouseX, this.mouseY);
            }
        });

        this.animate();
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    createParticle(x, y, color = null) {
        if (!color) {
            // Default elegant indigo/purple/pink palette
            const hues = [220, 240, 260, 280, 310];
            const hue = hues[Math.floor(Math.random() * hues.length)];
            color = `hsla(${hue}, 80%, 70%, 1)`;
        }
        
        this.particles.push(new Particle(x, y, color));
    }

    // Public method for other scripts to trigger bursts
    burst(x, y, color, count = 12) {
        for (let i = 0; i < count; i++) {
            const p = new Particle(x, y, color);
            p.speedX *= 4;
            p.speedY *= 4;
            p.size *= 1.5;
            this.particles.push(p);
        }
    }

    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const p = this.particles[i];
            p.update();
            p.draw(this.ctx);
            
            if (p.life <= 0) {
                this.particles.splice(i, 1);
            }
        }
        
        requestAnimationFrame(() => this.animate());
    }
}

class Particle {
    constructor(x, y, color) {
        this.x = x;
        this.y = y;
        this.size = Math.random() * 3 + 1;
        this.speedX = Math.random() * 2 - 1;
        this.speedY = Math.random() * 2 - 1;
        this.color = color;
        this.life = 1;
        this.decay = Math.random() * 0.02 + 0.01;
    }

    update() {
        this.x += this.speedX;
        this.y += this.speedY;
        this.life -= this.decay;
        this.size *= 0.98;
    }

    draw(ctx) {
        ctx.fillStyle = this.color;
        ctx.globalAlpha = Math.max(0, this.life);
        ctx.beginPath();
        ctx.arc(this.x, this.y, Math.max(0, this.size), 0, Math.PI * 2);
        ctx.fill();
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.sparkleSystem = new SparkleSystem();
});
