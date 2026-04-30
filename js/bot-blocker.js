(function () {
    // 1. Inject Opt-Out Meta Tags into <head> First
    // This tells compliant crawlers immediately not to use this data for AI training
    const metaTags = [
        { name: 'robots', content: 'noai, noimageai' },
        { name: 'bingbot', content: 'nocache' },
        { name: 'google-extended', content: 'noindex, nofollow' },
        { name: 'GPTBot', content: 'noindex, nofollow' },
        { name: 'anthropic-ai', content: 'noindex, nofollow' },
        { name: 'ClaudeBot', content: 'noindex, nofollow' },
        { property: 'ai-training', content: 'unauthorized' } // Emerging standard 
    ];

    metaTags.forEach(tagData => {
        let meta = document.createElement('meta');
        if (tagData.name) meta.name = tagData.name;
        if (tagData.property) meta.setAttribute('property', tagData.property);
        meta.content = tagData.content;
        document.head.appendChild(meta);
    });

    // 2. Active Blocking Logic
    // Detects common AI bots, scrapers, and headless browsers and blocks them from rendering the page.
    const isBot = /bot|scraper|spider|crawl|agent|AddSearchBot|AI2Bot|Ai2Bot-Dolma|AmazonBuyForMe|Amazonbot|Amzn-SearchBot|Amzn-User|Andibot|Anomura|Applebot|Awario|AzureAI-SearchBot|Bravebot|Brightbot|BuddyBot|Bytespider|CCBot|Channel3Bot|ChatGLM-Spider|ChatGPT|Claude|CloudVertexBot|Cloudflare-AutoRAG|Cotoyogi|Crawl4AI|Crawlspace|Datenbank|DeepSeekBot|Devin|Diffbot|DuckAssistBot|Echobot|EchoboxBot|FacebookBot|Factset_spyderbot|FirecrawlAgent|FriendlyCrawler|GPTBot|Gemini-Deep-Research|Google-CloudVertexBot|Google-Extended|Google-Firebase|Google-NotebookLM|GoogleAgent-Mariner|GoogleOther|ICC-Crawler|ISSCyberRiskCrawler|IbouBot|ImagesiftBot|Kangaroo|KlaviyoAIBot|KunatoCrawler|LAIONDownloader|LCC|LinerBot|Linguee|LinkupBot|Manus|Meta-ExternalAgent|Meta-ExternalFetcher|MistralAI|MyCentralAIScraperBot|NotebookLM|NovaAct|OAI-SearchBot|OpenAI|Operator|PanguBot|Panscient|Perplexity|PetalBot|PhindBot|Poggio-Citations|Poseidon|QualifiedBot|QuillBot|SBIntuitionsBot|Scrapy|SemrushBot|ShapBot|Sidetrade|Spider|TavilyBot|TerraCotta|Thinkbot|TikTokSpider|Timpibot|TwinAgent|VelenPublicWebCrawler|WARDBot|WRTNBot|Webzio-Extended|YaK|Yandex|YouBot|ZanistaBot|aiHitBot|amazon-kendra|anthropic-ai|atlassian-bot|bedrockbot|bigsur.ai|cohere-ai|cohere-training-data|facebookexternalhit|iAskBot|iaskspider|imageSpider|img2dataset|kagi-fetcher|laion-huggingface-processor|netEstate|omgili|panscient|quillbot|wpbot|HeadlessChrome|manus|OpenClaw|Clawdbot|Moltbot/i.test(navigator.userAgent);

    // Additional heuristics for headless browsers
    // We only use navigator.webdriver, as other checks (like !window.chrome) falsely flag Safari and Firefox.
    const isHeadless = navigator.webdriver === true;

    if (isBot || isHeadless) {
        // Clear the document body to prevent scraping of content
        document.documentElement.innerHTML = '';
        console.warn("Access denied. Automated scraping and AI data extraction is prohibited.");
    }
})();
