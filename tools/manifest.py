from dataclasses import dataclass

from tools.get_current_time import prompt as get_current_time_prompt
from tools.get_current_time.tool import TOOL as get_current_time_tool
from tools.todo_read import prompt as todo_read_prompt
from tools.todo_read.tool import TOOL as todo_read_tool
from tools.todo_write import prompt as todo_write_prompt
from tools.todo_write.tool import TOOL as todo_write_tool
from tools.checkpoint_history import prompt as checkpoint_history_prompt
from tools.checkpoint_history.tool import TOOL as checkpoint_history_tool
from tools.undo_last_change import prompt as undo_last_change_prompt
from tools.undo_last_change.tool import TOOL as undo_last_change_tool
from tools.reference_add import prompt as reference_add_prompt
from tools.reference_add.tool import TOOL as reference_add_tool
from tools.reference_list import prompt as reference_list_prompt
from tools.reference_list.tool import TOOL as reference_list_tool
from tools.reference_remove import prompt as reference_remove_prompt
from tools.reference_remove.tool import TOOL as reference_remove_tool
from tools.list_reference_dir import prompt as list_reference_dir_prompt
from tools.list_reference_dir.tool import TOOL as list_reference_dir_tool
from tools.read_reference_file import prompt as read_reference_file_prompt
from tools.read_reference_file.tool import TOOL as read_reference_file_tool
from tools.grep_reference import prompt as grep_reference_prompt
from tools.grep_reference.tool import TOOL as grep_reference_tool
from tools.list_files_in_dir import prompt as list_files_in_dir_prompt
from tools.list_files_in_dir.tool import TOOL as list_files_in_dir_tool
from tools.read_file import prompt as read_file_prompt
from tools.read_file.tool import TOOL as read_file_tool
from tools.memory_read import prompt as memory_read_prompt
from tools.memory_read.tool import TOOL as memory_read_tool
from tools.read_notebook import prompt as read_notebook_prompt
from tools.read_notebook.tool import TOOL as read_notebook_tool
from tools.read_image import prompt as read_image_prompt
from tools.read_image.tool import TOOL as read_image_tool
from tools.analyze_website import prompt as analyze_website_prompt
from tools.analyze_website.tool import TOOL as analyze_website_tool
from tools.delete_file import prompt as delete_file_prompt
from tools.delete_file.tool import TOOL as delete_file_tool
from tools.edit_file import prompt as edit_file_prompt
from tools.edit_file.tool import TOOL as edit_file_tool
from tools.multi_edit import prompt as multi_edit_prompt
from tools.multi_edit.tool import TOOL as multi_edit_tool
from tools.memory_write import prompt as memory_write_prompt
from tools.memory_write.tool import TOOL as memory_write_tool
from tools.edit_notebook import prompt as edit_notebook_prompt
from tools.edit_notebook.tool import TOOL as edit_notebook_tool
from tools.insert_notebook_cell import prompt as insert_notebook_cell_prompt
from tools.insert_notebook_cell.tool import TOOL as insert_notebook_cell_tool
from tools.delete_notebook_cell import prompt as delete_notebook_cell_prompt
from tools.delete_notebook_cell.tool import TOOL as delete_notebook_cell_tool
from tools.glob import prompt as glob_prompt
from tools.glob.tool import TOOL as glob_tool
from tools.git_status import prompt as git_status_prompt
from tools.git_status.tool import TOOL as git_status_tool
from tools.grep import prompt as grep_prompt
from tools.grep.tool import TOOL as grep_tool
from tools.run_command import prompt as run_command_prompt
from tools.run_command.tool import TOOL as run_command_tool
from tools.write_file import prompt as write_file_prompt
from tools.write_file.tool import TOOL as write_file_tool
from tools.change_workspace import prompt as change_workspace_prompt
from tools.change_workspace.tool import TOOL as change_workspace_tool
from tools.self_reflect import prompt as self_reflect_prompt
from tools.self_reflect.tool import TOOL as self_reflect_tool
from tools.task import prompt as task_prompt
from tools.task.tool import TOOL as task_tool
from tools.architect import prompt as architect_prompt
from tools.architect.tool import TOOL as architect_tool
from tools.mcp_list_servers import prompt as mcp_list_servers_prompt
from tools.mcp_list_servers.tool import TOOL as mcp_list_servers_tool
from tools.mcp_list_tools import prompt as mcp_list_tools_prompt
from tools.mcp_list_tools.tool import TOOL as mcp_list_tools_tool
from tools.mcp_call_tool import prompt as mcp_call_tool_prompt
from tools.mcp_call_tool.tool import TOOL as mcp_call_tool_tool
from tools.think import prompt as think_prompt
from tools.think.tool import TOOL as think_tool
from tools.sticker_request import prompt as sticker_request_prompt
from tools.sticker_request.tool import TOOL as sticker_request_tool
from tools.index_project import prompt as index_project_prompt
from tools.index_project.tool import TOOL as index_project_tool
from tools.project_overview import prompt as project_overview_prompt
from tools.project_overview.tool import TOOL as project_overview_tool
from tools.index_changed_files import prompt as index_changed_files_prompt
from tools.index_changed_files.tool import TOOL as index_changed_files_tool
from tools.search_project import prompt as search_project_prompt
from tools.search_project.tool import TOOL as search_project_tool
from tools.index_reference import prompt as index_reference_prompt
from tools.index_reference.tool import TOOL as index_reference_tool
from tools.reference_overview import prompt as reference_overview_prompt
from tools.reference_overview.tool import TOOL as reference_overview_tool
from tools.search_reference_project import prompt as search_reference_project_prompt
from tools.search_reference_project.tool import TOOL as search_reference_project_tool
from tools.search_symbols import prompt as search_symbols_prompt
from tools.search_symbols.tool import TOOL as search_symbols_tool


@dataclass(frozen=True)
class ToolModule:
    name: str
    prompt_module: object
    function: object


TOOL_MODULES = [
    ToolModule(get_current_time_prompt.TOOL_NAME, get_current_time_prompt, get_current_time_tool),
    ToolModule(todo_read_prompt.TOOL_NAME, todo_read_prompt, todo_read_tool),
    ToolModule(todo_write_prompt.TOOL_NAME, todo_write_prompt, todo_write_tool),
    ToolModule(checkpoint_history_prompt.TOOL_NAME, checkpoint_history_prompt, checkpoint_history_tool),
    ToolModule(undo_last_change_prompt.TOOL_NAME, undo_last_change_prompt, undo_last_change_tool),
    ToolModule(reference_add_prompt.TOOL_NAME, reference_add_prompt, reference_add_tool),
    ToolModule(reference_list_prompt.TOOL_NAME, reference_list_prompt, reference_list_tool),
    ToolModule(reference_remove_prompt.TOOL_NAME, reference_remove_prompt, reference_remove_tool),
    ToolModule(list_reference_dir_prompt.TOOL_NAME, list_reference_dir_prompt, list_reference_dir_tool),
    ToolModule(read_reference_file_prompt.TOOL_NAME, read_reference_file_prompt, read_reference_file_tool),
    ToolModule(grep_reference_prompt.TOOL_NAME, grep_reference_prompt, grep_reference_tool),
    ToolModule(list_files_in_dir_prompt.TOOL_NAME, list_files_in_dir_prompt, list_files_in_dir_tool),
    ToolModule(read_file_prompt.TOOL_NAME, read_file_prompt, read_file_tool),
    ToolModule(memory_read_prompt.TOOL_NAME, memory_read_prompt, memory_read_tool),
    ToolModule(read_notebook_prompt.TOOL_NAME, read_notebook_prompt, read_notebook_tool),
    ToolModule(read_image_prompt.TOOL_NAME, read_image_prompt, read_image_tool),
    ToolModule(analyze_website_prompt.TOOL_NAME, analyze_website_prompt, analyze_website_tool),
    ToolModule(delete_file_prompt.TOOL_NAME, delete_file_prompt, delete_file_tool),
    ToolModule(edit_file_prompt.TOOL_NAME, edit_file_prompt, edit_file_tool),
    ToolModule(multi_edit_prompt.TOOL_NAME, multi_edit_prompt, multi_edit_tool),
    ToolModule(memory_write_prompt.TOOL_NAME, memory_write_prompt, memory_write_tool),
    ToolModule(edit_notebook_prompt.TOOL_NAME, edit_notebook_prompt, edit_notebook_tool),
    ToolModule(insert_notebook_cell_prompt.TOOL_NAME, insert_notebook_cell_prompt, insert_notebook_cell_tool),
    ToolModule(delete_notebook_cell_prompt.TOOL_NAME, delete_notebook_cell_prompt, delete_notebook_cell_tool),
    ToolModule(glob_prompt.TOOL_NAME, glob_prompt, glob_tool),
    ToolModule(git_status_prompt.TOOL_NAME, git_status_prompt, git_status_tool),
    ToolModule(grep_prompt.TOOL_NAME, grep_prompt, grep_tool),
    ToolModule(run_command_prompt.TOOL_NAME, run_command_prompt, run_command_tool),
    ToolModule(write_file_prompt.TOOL_NAME, write_file_prompt, write_file_tool),
    ToolModule(change_workspace_prompt.TOOL_NAME, change_workspace_prompt, change_workspace_tool),
    ToolModule(self_reflect_prompt.TOOL_NAME, self_reflect_prompt, self_reflect_tool),
    ToolModule(task_prompt.TOOL_NAME, task_prompt, task_tool),
    ToolModule(architect_prompt.TOOL_NAME, architect_prompt, architect_tool),
    ToolModule(mcp_list_servers_prompt.TOOL_NAME, mcp_list_servers_prompt, mcp_list_servers_tool),
    ToolModule(mcp_list_tools_prompt.TOOL_NAME, mcp_list_tools_prompt, mcp_list_tools_tool),
    ToolModule(mcp_call_tool_prompt.TOOL_NAME, mcp_call_tool_prompt, mcp_call_tool_tool),
    ToolModule(think_prompt.TOOL_NAME, think_prompt, think_tool),
    ToolModule(sticker_request_prompt.TOOL_NAME, sticker_request_prompt, sticker_request_tool),
    ToolModule(index_project_prompt.TOOL_NAME, index_project_prompt, index_project_tool),
    ToolModule(project_overview_prompt.TOOL_NAME, project_overview_prompt, project_overview_tool),
    ToolModule(index_changed_files_prompt.TOOL_NAME, index_changed_files_prompt, index_changed_files_tool),
    ToolModule(search_project_prompt.TOOL_NAME, search_project_prompt, search_project_tool),
    ToolModule(index_reference_prompt.TOOL_NAME, index_reference_prompt, index_reference_tool),
    ToolModule(reference_overview_prompt.TOOL_NAME, reference_overview_prompt, reference_overview_tool),
    ToolModule(search_reference_project_prompt.TOOL_NAME, search_reference_project_prompt, search_reference_project_tool),
    ToolModule(search_symbols_prompt.TOOL_NAME, search_symbols_prompt, search_symbols_tool),
]
