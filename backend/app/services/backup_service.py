        except Exception as e:
            return {
                "component": "servers",
                "success": False,
                "error": str(e)
            }