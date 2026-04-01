# Skill: Add Monthly Images to Gallery

This skill automates the process of adding new monthly gallery images to the nuBlog site.

## Activation

User says: "add monthly images" or "update gallery with new images"

## Protocol

### Step 1: Discover New Images
1. Ask user which month/year gallery to update (or detect from context)
2. List files in the target directory sorted by modification time:
   ```bash
   ls -lt images/monthly/YYYY/MM-MMM/ | head -20
   ```
3. Identify new images (recently modified files)
4. Report count and filenames to user for confirmation

### Step 2: Compress Images
1. Run compression on the target directory:
   ```bash
   ./compress.sh images/monthly/YYYY/MM-MMM/
   ```
2. Report compression results (files processed, space saved)

### Step 3: Analyze Orientations
1. For each new image, check dimensions using `sips`:
   ```bash
   sips -g pixelWidth -g pixelHeight <image>
   ```
2. Classify as HORIZONTAL (width > height) or VERTICAL (height >= width)
3. Sort new images chronologically within each orientation group

### Step 4: Confirm Target Gallery
1. Ask user: "Which gallery page should these be added to?"
   - Provide choices based on detected month/year
   - Options: monthly galleries, camera galleries, misc galleries
   - Default to: `galleries/monthly/YYYY-MM-MMM.html`

### Step 5: Insert Images into HTML
1. Open the target gallery HTML file
2. Locate the split between horizontal and vertical sections
3. Insert new horizontal images at the END of the horizontal section (chronologically)
4. Insert new vertical images at the END of the vertical section (chronologically)
5. Use the format:
   ```html
   <div class="gallery-grid-item"><img src="../../images/monthly/YYYY/MM-MMM/IMG_XXXX.jpeg" alt="IMG_XXXX" class="styled-image" loading="lazy"></div>
   ```

### Step 6: Update Last Updated Date
1. Find the "last updated" line in `galleries/index.html` (typically line ~178)
2. Update to current date in format: `M/D/YYYY` (e.g., `4/1/2026`)
3. Example:
   ```html
   <i>last updated: 4/1/2026</i>
   ```

### Step 7: Commit and Push
1. Stage changes:
   ```bash
   git add galleries/monthly/YYYY-MM-MMM.html galleries/index.html
   ```
2. Commit with descriptive message:
   ```
   Add N new photos to MMM YYYY gallery
   
   Added X horizontal photos (IMG_XXXX, YYYY, ...)
   and Y vertical photos (IMG_ZZZZ, AAAA, ...) in chronological order,
   respecting the horizontal-first, vertical-second layout convention.
   
   Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
   ```
3. Push to remote:
   ```bash
   git push
   ```
4. Confirm success and provide link to updated gallery

## Key Conventions
- **Orientation Layout**: Horizontal photos displayed first, then vertical photos
- **Chronological Order**: Within each orientation group, photos sorted by filename (chronological)
- **No `.new-row` classes**: Let CSS Grid flow naturally
- **Path Format**: `../../images/monthly/YYYY/MM-MMM/IMG_XXXX.jpeg` (relative to gallery HTML)
- **Compression**: Always run compress.sh before adding to HTML

## Error Handling
- If compression fails: Report error, continue with uncompressed
- If orientation detection fails: Ask user to manually specify
- If target gallery not found: List available galleries and ask user to choose
- If git push fails: Report error and show git status

## Example Usage

**User**: "add monthly images"

**Agent**:
1. "Which month/year gallery? [Mar 2026 (current) | Feb 2026 | Jan 2026]"
2. User: "Mar 2026"
3. Discovers 9 new images in `images/monthly/2026/03-mar/`
4. Compresses images (saves 2.3MB)
5. Detects 6 horizontal, 3 vertical
6. Inserts into `galleries/monthly/2026-03-mar.html`
7. Updates last updated date in `galleries/index.html`
8. Commits and pushes
9. "✅ Added 9 photos to Mar 2026 gallery. Live at: https://llostinthesauce.github.io/galleries/monthly/2026-03-mar.html"

## Notes
- Always verify image paths before committing
- Check that images load properly in browser
- Update may take 1-2 minutes to deploy on GitHub Pages
- Keep this skill updated if gallery structure changes
