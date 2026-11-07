"""SQLAlchemy model modules.

The application imports each module before ``Base.metadata.create_all`` so
that additive tables are included in the metadata registry.
"""
