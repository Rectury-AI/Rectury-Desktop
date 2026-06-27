TOOL_NAME = 'sticker_request'
DESCRIPTION = 'Handle requests for stickers or swag in compact compatibility mode.'
PROMPT = '''Compact compatibility tool for sticker or swag requests. Use this
only if the user explicitly asks to receive stickers, swag, or merchandise.

This runtime cannot display shipping forms, collect mailing details, or send
stickers. When this tool is called, it returns an unavailable message so the
assistant can explain that the sticker request workflow is not supported here.

Do not use this tool for unrelated sticker work such as designing stickers,
storing sticker metadata, or implementing sticker UI.
'''
PARAMETERS = {
    'type': 'object',
    'properties': {
        'trigger': {
            'type': 'string',
            'description': 'The user phrase that explicitly requested stickers or swag',
        },
    },
    'required': ['trigger'],
    'additionalProperties': False,
}
