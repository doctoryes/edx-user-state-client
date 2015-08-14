import itertools

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver, Signal
from opaque_keys.edx.keys import CourseKey, UsageKey, BlockTypeKey


def _strip_object(key):
    """
    Strips branch and version info if the given key supports those attributes.
    """
    if hasattr(key, 'version_agnostic') and hasattr(key, 'for_branch'):
        return key.for_branch(None).version_agnostic()
    else:
        return key


def _strip_value(value, lookup='exact'):
    """
    Helper function to remove the branch and version information from the given value,
    which could be a single object or a list.
    """
    if lookup == 'in':
        stripped_value = [_strip_object(el) for el in value]
    else:
        stripped_value = _strip_object(value)
    return stripped_value


class OpaqueKeyField(models.CharField):
    """
    A django field for storing OpaqueKeys.

    The baseclass will return the value from the database as a string, rather than an instance
    of an OpaqueKey, leaving the application to determine which key subtype to parse the string
    as.

    Subclasses must specify a KEY_CLASS attribute, in which case the field will use :meth:`from_string`
    to parse the key string, and will return an instance of KEY_CLASS.
    """
    description = "An OpaqueKey object, saved to the DB in the form of a string."

    __metaclass__ = models.SubfieldBase

    Empty = object()
    KEY_CLASS = None

    def __init__(self, *args, **kwargs):
        if self.KEY_CLASS is None:
            raise ValueError('Must specify KEY_CLASS in OpaqueKeyField subclasses')

        super(OpaqueKeyField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if value is self.Empty or value is None:
            return None

        assert isinstance(value, (basestring, self.KEY_CLASS)), \
            "%s is not an instance of basestring or %s" % (value, self.KEY_CLASS)
        if value == '':
            # handle empty string for models being created w/o fields populated
            return None

        if isinstance(value, basestring):
            return self.KEY_CLASS.from_string(value)
        else:
            return value

    def get_prep_lookup(self, lookup, value):
        if lookup == 'isnull':
            raise TypeError('Use {0}.Empty rather than None to query for a missing {0}'.format(self.__class__.__name__))

        return super(OpaqueKeyField, self).get_prep_lookup(
            lookup,
            # strip key before comparing
            _strip_value(value, lookup)
        )

    def get_prep_value(self, value):
        if value is self.Empty or value is None:
            return ''  # CharFields should use '' as their empty value, rather than None

        assert isinstance(value, self.KEY_CLASS), "%s is not an instance of %s" % (value, self.KEY_CLASS)
        return unicode(_strip_value(value))

    def validate(self, value, model_instance):
        """Validate Empty values, otherwise defer to the parent"""
        # raise validation error if the use of this field says it can't be blank but it is
        if not self.blank and value is self.Empty:
            raise ValidationError(self.error_messages['blank'])
        else:
            return super(OpaqueKeyField, self).validate(value, model_instance)

    def run_validators(self, value):
        """Validate Empty values, otherwise defer to the parent"""
        if value is self.Empty:
            return

        return super(OpaqueKeyField, self).run_validators(value)


class CourseKeyField(OpaqueKeyField):
    """
    A django Field that stores a CourseKey object as a string.
    """
    description = "A CourseKey object, saved to the DB in the form of a string"
    KEY_CLASS = CourseKey


class UsageKeyField(OpaqueKeyField):
    """
    A django Field that stores a UsageKey object as a string.
    """
    description = "A Location object, saved to the DB in the form of a string"
    KEY_CLASS = UsageKey


def chunks(items, chunk_size):
    """
    Yields the values from items in chunks of size chunk_size
    """
    items = list(items)
    return (items[i:i + chunk_size] for i in xrange(0, len(items), chunk_size))


class ChunkingManager(models.Manager):
    """
    :class:`~Manager` that adds an additional method :meth:`chunked_filter` to provide
    the ability to make select queries with specific chunk sizes.
    """
    def chunked_filter(self, chunk_field, items, **kwargs):
        """
        Queries model_class with `chunk_field` set to chunks of size `chunk_size`,
        and all other parameters from `**kwargs`.

        This works around a limitation in sqlite3 on the number of parameters
        that can be put into a single query.

        Arguments:
            chunk_field (str): The name of the field to chunk the query on.
            items: The values for of chunk_field to select. This is chunked into ``chunk_size``
                chunks, and passed as the value for the ``chunk_field`` keyword argument to
                :meth:`~Manager.filter`. This implies that ``chunk_field`` should be an
                ``__in`` key.
            chunk_size (int): The size of chunks to pass. Defaults to 500.
        """
        chunk_size = kwargs.pop('chunk_size', 500)
        res = itertools.chain.from_iterable(
            self.filter(**dict([(chunk_field, chunk)] + kwargs.items()))
            for chunk in chunks(items, chunk_size)
        )
        return res


class StudentModule(models.Model):
    """
    Keeps student state for a particular module in a particular course.
    """
    objects = ChunkingManager()
    MODEL_TAGS = ['course_id', 'module_type']

    # For a homework problem, contains a JSON
    # object consisting of state
    MODULE_TYPES = (('problem', 'problem'),
                    ('video', 'video'),
                    ('html', 'html'),
                    ('course', 'course'),
                    ('chapter', 'Section'),
                    ('sequential', 'Subsection'),
                    ('library_content', 'Library Content'))
    ## These three are the key for the object
    module_type = models.CharField(max_length=32, choices=MODULE_TYPES, default='problem', db_index=True)

    # Key used to share state. This is the XBlock usage_id
    module_state_key = UsageKeyField(max_length=255, db_index=True, db_column='module_id')
    student = models.ForeignKey(User, db_index=True)

    course_id = CourseKeyField(max_length=255, db_index=True)

    class Meta(object):  # pylint: disable=missing-docstring
        unique_together = (('student', 'module_state_key', 'course_id'),)

    # Internal state of the object
    state = models.TextField(null=True, blank=True)

    # Grade, and are we done?
    grade = models.FloatField(null=True, blank=True, db_index=True)
    max_grade = models.FloatField(null=True, blank=True)
    DONE_TYPES = (
        ('na', 'NOT_APPLICABLE'),
        ('f', 'FINISHED'),
        ('i', 'INCOMPLETE'),
    )
    done = models.CharField(max_length=8, choices=DONE_TYPES, default='na', db_index=True)

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)

    @classmethod
    def all_submitted_problems_read_only(cls, course_id):
        """
        Return all model instances that correspond to problems that have been
        submitted for a given course. So module_type='problem' and a non-null
        grade. Use a read replica if one exists for this environment.
        """
        queryset = cls.objects.filter(
            course_id=course_id,
            module_type='problem',
            grade__isnull=False
        )
        if "read_replica" in settings.DATABASES:
            return queryset.using("read_replica")
        else:
            return queryset

    def __repr__(self):
        return 'StudentModule<%r>' % ({
            'course_id': self.course_id,
            'module_type': self.module_type,
            # We use the student_id instead of username to avoid a database hop.
            # This can actually matter in cases where we're logging many of
            # these (e.g. on a broken progress page).
            'student_id': self.student_id,  # pylint: disable=no-member
            'module_state_key': self.module_state_key,
            'state': str(self.state)[:20],
        },)

    def __unicode__(self):
        return unicode(repr(self))


class StudentModuleHistory(models.Model):
    """Keeps a complete history of state changes for a given XModule for a given
    Student. Right now, we restrict this to problems so that the table doesn't
    explode in size."""
    HISTORY_SAVING_TYPES = {'problem'}

    class Meta(object):  # pylint: disable=missing-docstring
        get_latest_by = "created"

    student_module = models.ForeignKey(StudentModule, db_index=True)
    version = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    # This should be populated from the modified field in StudentModule
    created = models.DateTimeField(db_index=True)
    state = models.TextField(null=True, blank=True)
    grade = models.FloatField(null=True, blank=True)
    max_grade = models.FloatField(null=True, blank=True)

    @receiver(post_save, sender=StudentModule)
    def save_history(sender, instance, **kwargs):  # pylint: disable=no-self-argument, unused-argument
        """
        Checks the instance's module_type, and creates & saves a
        StudentModuleHistory entry if the module_type is one that
        we save.
        """
        if instance.module_type in StudentModuleHistory.HISTORY_SAVING_TYPES:
            history_entry = StudentModuleHistory(student_module=instance,
                                                 version=None,
                                                 created=instance.modified,
                                                 state=instance.state,
                                                 grade=instance.grade,
                                                 max_grade=instance.max_grade)
            history_entry.save()
