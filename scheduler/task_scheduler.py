"""
Task scheduler module
Note: This module provides helper functions for scheduling.
Actual scheduling should be done via Windows Task Scheduler.
"""
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Task scheduler helper class"""

    @staticmethod
    def generate_windows_task_command(task_type: str, python_path: str = "python",
                                     script_path: str = None) -> str:
        """
        Generate Windows Task Scheduler command

        Args:
            task_type: Type of task (news, papers_patents, update_web)
            python_path: Path to Python executable
            script_path: Path to main.py script

        Returns:
            Command string for Windows Task Scheduler
        """
        if script_path is None:
            script_path = "C:\\path\\to\\manufacturing_info_spider\\main.py"

        command = f'"{python_path}" "{script_path}" --type {task_type}'

        return command

    @staticmethod
    def generate_task_xml(task_name: str, command: str, schedule: dict) -> str:
        """
        Generate XML for Windows Task Scheduler

        Args:
            task_name: Name of the task
            command: Command to execute
            schedule: Schedule configuration (days, time)

        Returns:
            XML string
        """
        # Days mapping
        days_map = {
            'MON': 'Monday',
            'TUE': 'Tuesday',
            'WED': 'Wednesday',
            'THU': 'Thursday',
            'FRI': 'Friday',
            'SAT': 'Saturday',
            'SUN': 'Sunday'
        }

        days_xml = ''.join([f'<{days_map[day]} />' for day in schedule.get('days', [])])
        time = schedule.get('time', '10:00')

        xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>{task_name} - Manufacturing Info Spider</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2024-01-01T{time}:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByWeek>
        <DaysOfWeek>
          {days_xml}
        </DaysOfWeek>
        <WeeksInterval>1</WeeksInterval>
      </ScheduleByWeek>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
  </Settings>
  <Actions>
    <Exec>
      <Command>{command.split()[0]}</Command>
      <Arguments>{' '.join(command.split()[1:])}</Arguments>
    </Exec>
  </Actions>
</Task>
"""
        return xml

    @staticmethod
    def print_setup_instructions():
        """Print instructions for setting up Windows Task Scheduler"""
        instructions = """
========================================
Windows Task Scheduler Setup Instructions
========================================

Option 1: Using Command Line (schtasks)
---------------------------------------

1. News Crawling (Every Monday, Wednesday, Friday at 10:00 AM):
   schtasks /create /tn "InfoSpider_News" /tr "python C:\\path\\to\\main.py --type news" /sc weekly /d MON,WED,FRI /st 10:00 /ru SYSTEM

2. Papers & Patents (Every Friday at 2:00 PM):
   schtasks /create /tn "InfoSpider_Papers_Patents" /tr "python C:\\path\\to\\main.py --type papers_patents" /sc weekly /d FRI /st 14:00 /ru SYSTEM

3. Website Update (Daily at 10:00 PM):
   schtasks /create /tn "InfoSpider_WebUpdate" /tr "python C:\\path\\to\\main.py --type update_web" /sc daily /st 22:00 /ru SYSTEM

Option 2: Using Task Scheduler GUI
----------------------------------

1. Open Task Scheduler (taskschd.msc)
2. Click "Create Task" in the right panel
3. General tab:
   - Name: InfoSpider_News (or other task name)
   - Description: Crawl manufacturing news
   - Run whether user is logged on or not: Yes
4. Triggers tab:
   - New -> Weekly -> Select days -> Set time
5. Actions tab:
   - New -> Start a program
   - Program/script: python (or full path to python.exe)
   - Arguments: C:\\path\\to\\main.py --type news
6. Click OK to save

Option 3: Manual Execution for Testing
--------------------------------------

Test each task type before scheduling:

python main.py --type news --test
python main.py --type papers_patents --test
python main.py --type update_web

Verify Tasks
-----------

List all scheduled tasks:
schtasks /query /tn "InfoSpider*" /fo LIST /v

Delete a task:
schtasks /delete /tn "InfoSpider_News" /f

========================================
"""
        print(instructions)
        return instructions

    @staticmethod
    def should_run_news_crawl() -> bool:
        """
        Check if news crawl should run today

        Returns:
            True if today is MON, WED, or FRI
        """
        today = datetime.now().strftime('%a').upper()
        return today in ['MON', 'WED', 'FRI']

    @staticmethod
    def should_run_papers_patents_crawl() -> bool:
        """
        Check if papers/patents crawl should run today

        Returns:
            True if today is FRI
        """
        today = datetime.now().strftime('%a').upper()
        return today == 'FRI'

    @staticmethod
    def get_next_run_time(task_type: str) -> Optional[str]:
        """
        Get next run time for a task type

        Args:
            task_type: Type of task

        Returns:
            Next run time as string or None
        """
        from config.settings import NEWS_SCHEDULE, PAPERS_PATENTS_SCHEDULE, WEB_UPDATE_SCHEDULE

        schedule_map = {
            'news': NEWS_SCHEDULE,
            'papers_patents': PAPERS_PATENTS_SCHEDULE,
            'update_web': WEB_UPDATE_SCHEDULE
        }

        schedule = schedule_map.get(task_type)
        if not schedule:
            return None

        # This is a simplified implementation
        # In production, calculate actual next run time based on schedule
        return f"{schedule['days'][0] if schedule['days'] else 'N/A'} at {schedule['time']}"
