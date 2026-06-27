# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `analyze_website` tool.

TOOL_NAME = 'analyze_website'
PROMPT = 'Fetch and analyze a public website URL. Extracts visible text, title, metadata, headings, internal/external links, images, forms, scripts, stylesheets, and can crawl same-site internal pages. Use this when the user passes a URL or asks what is on a website, how it is structured, what links/pages it has, or wants website content inspected.'
PARAMETERS = {'type': 'object',
 'properties': {'url': {'type': 'string',
                        'description': 'HTTP or HTTPS website URL to inspect. A '
                                       'missing scheme defaults to https.'},
                'crawl': {'type': 'boolean',
                          'description': 'Whether to follow same-site internal links '
                                         'after the first page',
                          'default': True},
                'max_pages': {'type': 'integer',
                              'minimum': 1,
                              'maximum': 20,
                              'description': 'Maximum same-site pages to fetch',
                              'default': 5},
                'max_depth': {'type': 'integer',
                              'minimum': 0,
                              'maximum': 3,
                              'description': 'Maximum internal-link crawl depth from '
                                             'the start URL',
                              'default': 1},
                'include_assets': {'type': 'boolean',
                                   'description': 'Include image, script, and '
                                                  'stylesheet URL lists in the result',
                                   'default': True}},
 'required': ['url'],
 'additionalProperties': False}
