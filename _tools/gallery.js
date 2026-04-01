// Render gallery groups from gallery-data.js
document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('[data-gallery-groups]');
    if (container && window.nublogGalleryGroups) {
        const groupTemplate = document.getElementById('gallery-group-template');
        const entryTemplate = document.getElementById('gallery-entry-template');
        
        window.nublogGalleryGroups.forEach(group => {
            const groupClone = groupTemplate.content.cloneNode(true);
            const title = groupClone.querySelector('.gallery-group-title');
            const note = groupClone.querySelector('.gallery-group-note');
            const grid = groupClone.querySelector('.gallery-grid');
            
            title.textContent = group.title || '';
            if (group.note) {
                note.textContent = group.note;
            } else {
                note.remove();
            }
            
            group.entries.forEach(entry => {
                const entryClone = entryTemplate.content.cloneNode(true);
                const link = entryClone.querySelector('.gallery-entry-label');
                const entryDiv = entryClone.querySelector('.gallery-entry');
                
                link.textContent = entry.label || '';
                link.href = entry.href || '#';
                
                if (entry.disabled) {
                    link.classList.add('is-disabled');
                }
                
                if (entry.previewImage) {
                    entryDiv.classList.add('gallery-entry-preview');
                    entryDiv.style.backgroundImage = `url(../${entry.previewImage})`;
                }
                
                grid.appendChild(entryClone);
            });
            
            container.appendChild(groupClone);
        });
    }
    
    // Load-more functionality for individual gallery pages
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
