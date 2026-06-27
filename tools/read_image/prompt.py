# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `read_image` tool.

TOOL_NAME = 'read_image'
PROMPT = 'Read image metadata and optionally include a data URL for a PNG, JPEG, GIF, or WebP file inside the active workspace. Use this when screenshots, UI captures, or visual assets matter.'
PARAMETERS = {'type': 'object',
 'properties': {'file_path': {'type': 'string',
                              'description': 'Path to an image file inside the active '
                                             'workspace'},
                'include_data': {'type': 'boolean',
                                 'description': 'Include a base64 data URL when the '
                                                'image is small enough',
                                 'default': True}},
 'required': ['file_path'],
 'additionalProperties': False}
