# Video Embedding Guide for Galleries

This guide explains how to embed videos into your image galleries.

## Overview

The gallery system now supports both images and videos within the same `.gallery-grid` layout. Videos are styled to match images and fit seamlessly into the responsive grid.

## Basic Video Embedding

To add a video to any gallery page, use the standard HTML5 `<video>` element within a `.gallery-grid-item` div:

```html
<div class="gallery-grid-item">
    <video controls class="styled-image">
        <source src="../../videos/your-video.mp4" type="video/mp4">
        <source src="../../videos/your-video.webm" type="video/webm">
        Your browser does not support the video tag.
    </video>
    <p>Optional caption for the video</p>
</div>
```

## Video Attributes

### Required
- `class="styled-image"` - Applies the gallery styling to ensure proper sizing and responsiveness

### Recommended
- `controls` - Displays play/pause, volume, and other playback controls
- Multiple `<source>` elements - Provides fallback formats for browser compatibility

### Optional
- `autoplay` - Video starts playing automatically (must be combined with `muted`)
- `muted` - Mutes the video audio (required for autoplay on most browsers)
- `loop` - Video repeats continuously
- `playsinline` - Plays inline on mobile devices (prevents fullscreen)
- `preload="metadata"` - Preloads video metadata only (file size, duration, etc.)
- `poster="path/to/image.jpeg"` - Shows a thumbnail image before the video plays

## Examples

### Example 1: Basic Video with Controls
```html
<div class="gallery-grid-item">
    <video controls class="styled-image">
        <source src="../../videos/my-video.mp4" type="video/mp4">
        Your browser does not support the video tag.
    </video>
    <p>My video description</p>
</div>
```

### Example 2: Auto-playing Looping Video (Like a GIF)
```html
<div class="gallery-grid-item">
    <video autoplay muted loop playsinline class="styled-image">
        <source src="../../videos/loop-animation.mp4" type="video/mp4">
        Your browser does not support the video tag.
    </video>
</div>
```

### Example 3: Video with Poster Image
```html
<div class="gallery-grid-item">
    <video controls preload="metadata" poster="../../images/video-thumbnail.jpeg" class="styled-image">
        <source src="../../videos/documentary.mp4" type="video/mp4">
        Your browser does not support the video tag.
    </video>
    <p>Documentary clip</p>
</div>
```

### Example 4: Mixed Image and Video Gallery
```html
<div class="gallery-grid">
    <!-- Image -->
    <div class="gallery-grid-item">
        <img src="../../images/photo1.jpeg" alt="Photo" class="styled-image" loading="lazy">
        <p>A photo</p>
    </div>

    <!-- Video -->
    <div class="gallery-grid-item">
        <video controls class="styled-image">
            <source src="../../videos/clip.mp4" type="video/mp4">
            Your browser does not support the video tag.
        </video>
        <p>A video</p>
    </div>

    <!-- Another image -->
    <div class="gallery-grid-item">
        <img src="../../images/photo2.jpeg" alt="Photo 2" class="styled-image" loading="lazy">
    </div>
</div>
```

## Video Formats

### Recommended Formats
- **MP4 (H.264)** - Best browser compatibility, supported everywhere
- **WebM (VP9)** - Modern format, good compression, open source

### Multiple Format Example
Provide multiple formats for maximum compatibility:

```html
<video controls class="styled-image">
    <source src="../../videos/video.mp4" type="video/mp4">
    <source src="../../videos/video.webm" type="video/webm">
    Your browser does not support the video tag.
</video>
```

Browsers will automatically select the first format they support.

## File Organization

Store video files in a dedicated videos folder:
```
/
├── images/
│   ├── monthly/
│   └── misc/
├── videos/          ← Create this folder
│   ├── monthly/
│   └── misc/
└── galleries/
    ├── monthly/
    └── misc/
```

## Performance Tips

1. **Optimize video files**: Compress videos before uploading to reduce file size
2. **Use `preload="metadata"`**: Only loads video metadata initially, not the entire file
3. **Add poster images**: Provides instant visual feedback while video loads
4. **Consider file size**: Large videos can slow down page load times
5. **Use lazy loading libraries**: For galleries with many videos, consider implementing lazy loading

## Browser Compatibility

The video implementation uses standard HTML5 video, which is supported by:
- Chrome/Edge (all versions)
- Firefox (all versions)
- Safari (all versions)
- Mobile browsers (iOS Safari, Chrome Mobile, etc.)

Always include the fallback text "Your browser does not support the video tag" for very old browsers.

## Live Example

See `/galleries/misc/video-example.html` for a working example of videos embedded in a gallery.

## Accessibility

For better accessibility, consider:
- Adding meaningful captions in the `<p>` tag
- Including transcripts for important video content
- Using descriptive file names

## Working with Existing Galleries

Videos integrate seamlessly with all existing gallery features:
- ✅ Responsive grid layout
- ✅ Load more functionality (`gallery.js`)
- ✅ Mixed with images
- ✅ Batch loading
- ✅ Mobile-friendly

Simply add video elements anywhere you would add an image element!
