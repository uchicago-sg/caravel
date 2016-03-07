def gae_mini_profiler_should_profile_production():
    from google.appengine.api import users
    return users.is_current_user_admin()
