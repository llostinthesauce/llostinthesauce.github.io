(function () {
    const groups = window.nublogGalleryGroups || [];
    const container = document.querySelector('[data-gallery-groups]');
    if (!container || !groups.length) {
        return;
    }

    const groupTemplate = document.getElementById('gallery-group-template');
    const entryTemplate = document.getElementById('gallery-entry-template');
    if (!groupTemplate || !entryTemplate) {
        return;
    }

    const base = (window.nublogBase || '.').replace(/\/+$/, '') || '.';
    const joinPath = (path) => `${base}/${String(path || '').replace(/^\//, '')}`;

    groups.forEach((group) => {
        if (!group || group.hidden) {
            return;
        }

        const entries = (group.entries || []).filter((entry) => entry && !entry.hidden);
        if (!entries.length) {
            return;
        }

        const groupNode = groupTemplate.content.cloneNode(true);
        const section = groupNode.querySelector('.gallery-group');
        const title = groupNode.querySelector('.gallery-group-title');
        const note = groupNode.querySelector('.gallery-group-note');
        const grid = groupNode.querySelector('.gallery-grid');

        if (group.className && section) {
            section.classList.add(group.className);
        }

        if (!grid) {
            return;
        }

        if (Number.isFinite(group.minWidth)) {
            grid.style.setProperty('--gallery-min-width', `${group.minWidth}px`);
        }

        if (title) {
            if (group.title) {
                title.textContent = group.title;
            } else {
                title.remove();
            }
        }

        if (note) {
            if (group.note) {
                note.textContent = group.note;
            } else {
                note.remove();
            }
        }

        const renderEntry = (entry, targetGrid) => {
            const entryNode = entryTemplate.content.cloneNode(true);
            const wrapper = entryNode.querySelector('.gallery-entry');
            const label = entryNode.querySelector('.gallery-entry-label');
            const childrenGrid = entryNode.querySelector('.gallery-entry-children');

            if (wrapper && entry.className) {
                wrapper.classList.add(entry.className);
            }
            if (wrapper && entry.previewImage) {
                wrapper.classList.add('gallery-entry-preview');
                wrapper.style.backgroundImage = `url('${joinPath(entry.previewImage)}')`;
            }

            if (label) {
                label.textContent = entry.label || entry.href || 'untitled';
                if (entry.title) {
                    label.title = entry.title;
                }

                if (entry.href && !entry.disabled) {
                    label.href = joinPath(entry.href);
                } else {
                    label.removeAttribute('href');
                    label.classList.add('is-disabled');
                }
            }

            if (childrenGrid) {
                const children = (entry.children || []).filter((child) => child && !child.hidden);
                if (Number.isFinite(entry.childrenMinWidth)) {
                    childrenGrid.style.setProperty('--gallery-child-min-width', `${entry.childrenMinWidth}px`);
                }

                if (children.length) {
                    children.forEach((child) => renderEntry(child, childrenGrid));
                } else {
                    childrenGrid.remove();
                }
            }

            targetGrid.appendChild(entryNode);
        };

        entries.forEach((entry) => renderEntry(entry, grid));

        container.appendChild(groupNode);
    });
})();
