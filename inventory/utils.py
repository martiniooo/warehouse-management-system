from .models import Location

def suggest_location(required_volume):
    locations = Location.objects.all()

    suitable_locations = [
        loc for loc in locations
        if loc.free_capacity() >= required_volume
    ]

    if not suitable_locations:
        return None

    suitable_locations.sort(
        key=lambda loc: loc.free_capacity(),
        reverse=True
    )

    return suitable_locations[0]

def user_has_role(user, roles):
    if not user.is_authenticated:
        return False
    return hasattr(user, 'userprofile') and user.userprofile.role in roles

