User Roles
==========

The application supports two roles: ``user`` and ``admin``.

Admin bootstrap
---------------

The first administrator is created through server configuration. Add one or
more emails to ``ADMIN_EMAILS`` before registration:

.. code-block:: text

   ADMIN_EMAILS=admin@example.com,owner@example.com

When a user registers with one of these emails, the account receives the
``admin`` role automatically. Regular registration requests cannot choose a
role.

Role assignment
---------------

After an admin account exists, it can assign roles through the protected
endpoint:

.. code-block:: text

   PATCH /users/{user_id}/role
   Authorization: Bearer <admin_token>
   Content-Type: application/json

   {"role": "admin"}

Only authenticated users with role ``admin`` can call this endpoint. Non-admin
users receive ``403 Forbidden``.
