const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const galleryDirs = [
    'galleries/monthly',
    'galleries/cameras',
    'galleries/misc'
];

function getDimensions(filePath) {
    try {
        const output = execSync(`sips -g pixelWidth -g pixelHeight "${filePath}"`).toString();
        const widthMatch = output.match(/pixelWidth: (\d+)/);
        const heightMatch = output.match(/pixelHeight: (\d+)/);
        if (widthMatch && heightMatch) {
            return {
                width: parseInt(widthMatch[1]),
                height: parseInt(heightMatch[1])
            };
        }
    } catch (e) {
        // console.error(`Error getting dimensions for ${filePath}: ${e.message}`);
    }
    return null;
}

galleryDirs.forEach(dir => {
    const files = fs.readdirSync(dir).filter(f => f.endsWith('.html'));
    files.forEach(file => {
        const filePath = path.join(dir, file);
        const content = fs.readFileSync(filePath, 'utf8');
        const imgRegex = /<img[^>]+src="([^"]+)"/g;
        let match;
        const images = [];
        while ((match = imgRegex.exec(content)) !== null) {
            images.push(match[1]);
        }

        if (images.length === 0) return;

        let firstVertical = null;
        for (const imgSrc of images) {
            // Resolve path relative to the html file
            let absoluteImgPath;
            if (imgSrc.startsWith('../../')) {
                absoluteImgPath = path.resolve(dir, imgSrc);
            } else if (imgSrc.startsWith('../../../')) {
                absoluteImgPath = path.resolve(dir, imgSrc);
            } else {
                absoluteImgPath = path.resolve(dir, imgSrc);
            }

            const dims = getDimensions(absoluteImgPath);
            if (dims && dims.height > dims.width) {
                firstVertical = imgSrc;
                break;
            }
        }

        if (firstVertical) {
            console.log(`${filePath}: ${firstVertical}`);
        } else {
            console.log(`${filePath}: No vertical images found`);
        }
    });
});
