document.addEventListener('DOMContentLoaded', () => {
    const BATCH_SIZE = 21;
    const items = Array.from(document.querySelectorAll('.gallery-grid-item'));
    const grid = document.querySelector('.gallery-grid');
    if (!grid || items.length <= BATCH_SIZE) return;

    const loadMoreBtn = document.createElement('button');
    loadMoreBtn.className = 'load-more-btn';
    grid.after(loadMoreBtn);
    
    let visibleCount = BATCH_SIZE;
    const updateVisibility = () => {
        items.forEach((item, i) => {
            if (i < visibleCount) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
        const remaining = items.length - visibleCount;
        if (remaining <= 0) {
            loadMoreBtn.style.display = 'none';
        } else {
            loadMoreBtn.style.display = 'block';
            const nextBatch = Math.min(BATCH_SIZE, remaining);
            loadMoreBtn.textContent = `Load More (${nextBatch} more images)`;
        }
    };

    loadMoreBtn.addEventListener('click', () => {
        visibleCount += BATCH_SIZE;
        updateVisibility();
    });
    updateVisibility();
});
