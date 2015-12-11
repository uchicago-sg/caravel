import os
import re
import time
import uuid
import cloudstorage
from google.appengine.ext import ndb
from google.appengine.api import images

class PhotoProperty(ndb.StringProperty):
    """
    A PhotoProperty is a representation of a photo reference in the datastore.
    """

    def _validate(self, value):
        """Ensures that this is actually a Photo."""

        if value and not isinstance(value, Photo):
            raise TypeError(value)

    def _to_base_type(self, value):
        """Encodes this photo as a string."""
        return value.path

    def _from_base_type(self, value):
        """Reads the photo from the datastore."""
        return Photo(value)

class PhotosMixin(ndb.Model):
    photos = PhotoProperty(repeated=True)

    @property
    def uploaded_photos(self):
        """Nasty hack(tm) to allow wtforms to edit the photos property."""

        class Pointer(object):
            def __init__(self, index):
                self.index = index
            
            @property
            def image(_self):
                return self.photos[_self.index]
            
            @image.setter
            def image(_self, value):
                while len(self.photos) <= _self.index:
                    self.photos.append(None)
                self.photos[_self.index] = value

        return [Pointer(i) for i in xrange(5)]

    @uploaded_photos.setter
    def uploaded_photos(self, photos):
        """Nasty hack(tm) to allow wtforms to edit the photos property."""

        self.photos = [p for p in self.photos if p]

class Photo(object):
    APP_ID = os.environ.get("APPLICATION_ID", "app~id")
    GCS_BUCKET = (re.sub(r'[^a-zA-Z\-]', '', APP_ID.split("~")[1]) +
                     ".appspot.com")

    @classmethod
    def from_image_data(klass, image_data):
        """
        Uploads and stores the given buffer of image data.
        Returns a Photo object.
        """

        # Create a sequential ID number for each photo.
        path = "{}-{}".format(int(time.time()), uuid.uuid4())

        for name, size, crop in [("small", 300, True), ("large", 600, False)]:

            # Transform photo to look nice.
            img = images.Image(image_data)
            img.resize(size, size, crop_to_fit=crop)
            img.im_feeling_lucky()
            resized = img.execute_transforms(output_encoding=images.JPEG)

            # Save it to GCS.
            output_file = cloudstorage.open(
                filename="/{}/{}-{}".format(klass.GCS_BUCKET, path, name),
                mode="w",
                content_type="image/jpg",
                options={"x-goog-acl": "public-read"}
            )
            output_file.write(resized)
            output_file.close()

        return klass(path)

    @classmethod
    def remove_old_photos(self, max_age=3600*24*30):
        """
        Removes all files from the GCS bucket older than the given age.
        """

        for entry in cloudstorage.listbucket("/" + self.GCS_BUCKET):
            try:
                when, _ = entry.filename.split("-", 1)
                age = time.time() - int(when)
                if age > max_age:
                    cloudstorage.delete(entry.filename)

            except ValueError:
                pass

    def __init__(self, path):
        """
        Create a Photo object from its string representation.
        """

        self.path = path

    def gcs_filename(self, size=None):
        """
        Returns the bucket key item for this photo, when stored in the given
        size.
        """

        return "/{}/{}-{}".format(self.GCS_BUCKET, self.path, size)

    def read(self, size=None):
        """
        Returns the image data of this photo with the given size.
        """

        return cloudstorage.open(filename=self.gcs_filename(size)).read()

    def public_url(self, size=None):
        """
        Returns a public URL for the photo of the given size.
        """

        if os.environ["SERVER_SOFTWARE"].startswith("Development/"):
            return "/_ah/gcs" + self.gcs_filename(size)
        else:
            return "https://storage.googleapis.com" + self.gcs_filename(size)

    def sizes(self):
        """
        Returns a list of all available sizes of this photo.
        """

        inodes = cloudstorage.listbucket(path_prefix="/{}/{}".format(
                        self.GCS_BUCKET, self.path))
        return [inode.filename.split("-")[-1] for inode in inodes]
