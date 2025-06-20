// Custom JavaScript for Test That documentation

document.addEventListener('DOMContentLoaded', function() {
    // Add copy functionality for code blocks that don't have it
    document.querySelectorAll('pre code').forEach(function(block) {
        if (!block.parentElement.querySelector('.md-clipboard')) {
            // Add copy button functionality
            block.addEventListener('click', function() {
                navigator.clipboard.writeText(block.textContent);
                
                // Show brief feedback
                const feedback = document.createElement('div');
                feedback.textContent = 'Copied!';
                feedback.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: var(--md-primary-fg-color);
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    z-index: 1000;
                    opacity: 0.9;
                `;
                document.body.appendChild(feedback);
                
                setTimeout(() => {
                    document.body.removeChild(feedback);
                }, 1000);
            });
        }
    });

    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Enhance code examples with run buttons (placeholder for future)
    document.querySelectorAll('pre code.language-python').forEach(function(block) {
        const pre = block.parentElement;
        
        // Add a subtle indicator that this is runnable code
        if (block.textContent.includes('from that import')) {
            pre.setAttribute('title', 'Test That example - click to copy');
            pre.style.cursor = 'pointer';
        }
    });
});