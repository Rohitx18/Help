async def update(self, taskId: str, action: str, content: Optional[str] = None, comments: Optional[str] = None):
    # Retrieve the task
    task: ProcessingTask = self.task_service_dao.get(taskId=taskId)
    current_user = self.userModel.userId

    # Dictionary for storing updates
    updateConfig = {}

    # **LOCKED Action**
    if action == "LOCKED":
        # Check if the current user is a Maker
        if not self.userModel.isMaker:
            raise Exception("Only Makers can lock the document.")
        
        # Check if already locked
        if task.LOCKED_BY and task.LOCKED_BY.get("isLocked", False):
            raise Exception("The document is already locked.")

        # Set lock details
        updateConfig[ProcessingTask.LOCKED_BY] = {
            "isLocked": True,
            "lockedBy": self.userModel.dict(),  # Assuming userModel has a method to convert to dict
            "timestamp": datetime.utcnow()
        }

    # **SAVED Action**
    elif action == "SAVED":
        # Check if document is locked
        if not task.LOCKED_BY or not task.LOCKED_BY.get("isLocked", False):
            raise Exception("Document must be locked before saving.")

        # Check if current user is the locker
        if task.LOCKED_BY["lockedBy"]["userId"] != current_user:
            raise Exception("Only the user who locked the document can save it.")

        # Update OUTPUT and MODIFIED_BY
        updateConfig[ProcessingTask.OUTPUT] = content
        updateConfig[ProcessingTask.MODIFIED_BY] = {
            "userModel": self.userModel.dict(),
            "timestamp": datetime.utcnow()
        }
        updateConfig[ProcessingTask.MODIFIED_TS] = datetime.utcnow()

    # **UNLOCKED Action**
    elif action == "UNLOCKED":
        # Check if current user is the one who locked the document
        if not task.LOCKED_BY or task.LOCKED_BY["lockedBy"]["userId"] != current_user:
            raise Exception("Only the user who locked the document can unlock it.")

        # Clear LOCKED_BY details
        updateConfig[ProcessingTask.LOCKED_BY] = None

    # **REVIEW_REQUEST Action**
    elif action == "REVIEW_REQUEST":
        # Check if user is a Maker
        if not self.userModel.isMaker:
            raise Exception("Only Makers can request a review.")

        # If locked, check if the locker is the current user
        if task.LOCKED_BY and task.LOCKED_BY.get("isLocked", False) and task.LOCKED_BY["lockedBy"]["userId"] != current_user:
            raise Exception("Only the user who locked the document can request a review while it is locked.")

        # Update the STATUS for review
        updateConfig[ProcessingTask.STATUS] = "REVIEW_REQUEST"

    # **APPROVED / REJECTED Actions for Checker**
    elif action in {"APPROVED", "REJECTED"}:
        # Check if user is authorized as Checker and not Maker simultaneously
        if not self.userModel.isChecker or (self.userModel.isChecker and self.userModel.isMaker):
            raise Exception("Only a user with Checker-only authorization can approve or reject.")

        # Update the STATUS and comments if provided
        updateConfig[ProcessingTask.STATUS] = action
        if action == "REJECTED" and comments:
            updateConfig["comments"] = comments

    # Apply updates to the database
    self.task_service_dao.update(taskId=taskId, updateConfig=updateConfig)
