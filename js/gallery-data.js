// gallery-data.js — nuBlog gallery index
//
// Keep `sourceImage` pointed at the original and use its generated thumbnail
// for `previewImage`, both relative to the site root.
//
// Emphasis is data, not position:
//   featured: true   purple pin, no badge. Evergreen — the current month.
//                    Pinned cards don't carry `added`; they never compete for
//                    the '*new!' badge.
//   added: 'YYYY-MM' when the entry appeared. js/whats-new.js badges the
//                    newest one in the group and drops it after 90 days.

window.nublogGalleryGroups = [
    {
        title: '',
        entries: [
            {
                label: 'july 2026 ~ current',
                href: 'galleries/monthly/2026-07-jul.html',
                sourceImage: 'images/monthly/2026/07-jul/IDG_20260712_160939_IMG_5436.jpg',
                previewImage: 'images/.thumbs/monthly/2026/07-jul/IDG_20260712_160939_IMG_5436.jpg',
                featured: true
            },
            {
                label: 'canon eos elan ii 35mm',
                href: 'galleries/cameras/canon-elan-ii.html',
                sourceImage: 'images/cameras/elan-ii/roll-2/R1-08312-0020.JPG',
                previewImage: 'images/.thumbs/cameras/elan-ii/roll-2/R1-08312-0020.jpg',
                added: '2026-06'
            },
            {
                label: 'vivitar pz3090 35mm',
                href: 'galleries/cameras/vivitar-pz3090.html',
                sourceImage: 'images/cameras/vivitar/roll-4/R1-08311-009A.JPG',
                previewImage: 'images/.thumbs/cameras/vivitar/roll-4/R1-08311-009A.jpg',
                added: '2026-04'
            },
            {
                label: 'disposable 35mm',
                href: 'galleries/cameras/disposable.html',
                sourceImage: 'images/cameras/disposable/k8.jpeg',
                previewImage: 'images/.thumbs/cameras/disposable/k8.jpg',
                added: '2026-04'
            },
            {
                label: 'canon sd400 digital',
                href: 'galleries/cameras/canon-sd400.html',
                sourceImage: 'images/cameras/canon/2026/IMG_4010.jpeg',
                previewImage: 'images/.thumbs/cameras/canon/2026/IMG_4010.jpg',
                added: '2026-04'
            },
            {
                label: 'plants',
                href: 'plants.html',
                sourceImage: 'images/plants/plantos4.JPG',
                previewImage: 'images/.thumbs/plants/plantos4.jpg',
                added: '2026-04'
            },
            {
                label: 'animals',
                href: 'galleries/animals.html',
                sourceImage: 'images/galleries/animals.jpeg',
                previewImage: 'images/.thumbs/galleries/animals.jpg',
                added: '2026-04'
            },

            {
                label: 'videos',
                href: 'galleries/videos.html',
                sourceImage: 'images/galleries/videos.jpeg',
                previewImage: 'images/.thumbs/galleries/videos.jpg',
                added: '2026-04'
            }
        ]
    },
    {
        title: '2026',
        entries: [
            {
                label: 'jul 2026',
                href: 'galleries/monthly/2026-07-jul.html',
                caption: ''
            },
            {
                label: 'june 2026',
                href: 'galleries/monthly/2026-06-june.html',
                caption: ''
            },
            {
                label: 'may 2026',
                href: 'galleries/monthly/2026-05-may.html',
                caption: ''
            },
            {
                label: 'apr 2026',
                href: 'galleries/monthly/2026-04-apr.html',
                caption: ''
            },
            {
                label: 'mar 2026',
                href: 'galleries/monthly/2026-03-mar.html',
                caption: ''
            },
            {
                label: 'feb 2026',
                href: 'galleries/monthly/2026-02-feb.html',
                caption: ''
            },
            {
                label: 'jan 2026',
                href: 'galleries/monthly/2026-01-jan.html',
                caption: ''
            }
        ]
    },
    {
        title: '2025',
        entries: [
            {
                label: 'dec 2025',
                href: 'galleries/monthly/2025-12-dec.html',
                caption: ''
            },
            {
                label: 'nov 2025',
                href: 'galleries/monthly/2025-11-nov.html',
                caption: ''
            },
            {
                label: 'oct 2025',
                href: 'galleries/monthly/2025-10-oct.html',
                caption: ''
            },
            {
                label: 'sep 2025',
                href: 'galleries/monthly/2025-09-sep.html',
                caption: ''
            },
            {
                label: 'aug 2025',
                href: 'galleries/monthly/2025-08-aug.html',
                caption: ''
            },
            {
                label: 'jul 2025',
                href: 'galleries/monthly/2025-07-jul.html',
                caption: ''
            },
            {
                label: 'jun 2025',
                href: 'galleries/monthly/2025-06-jun.html',
                caption: ''
            },
            {
                label: 'may 2025',
                href: 'galleries/monthly/2025-05-may.html',
                caption: ''
            },
            {
                label: 'apr 2025',
                href: 'galleries/monthly/2025-04-apr.html',
                caption: ''
            },
            {
                label: 'mar 2025',
                href: 'galleries/monthly/2025-03-mar.html',
                caption: ''
            },
            {
                label: 'feb 2025',
                href: 'galleries/monthly/2025-02-feb.html',
                caption: ''
            },
            {
                label: 'jan 2025',
                href: 'galleries/monthly/2025-01-jan.html',
                caption: ''
            }
        ]
    }
];
