from whitenoise.storage import CompressedManifestStaticFilesStorage


class StaticStorage(CompressedManifestStaticFilesStorage):
    """WhiteNoise-хранилище, которое не переписывает `sourceMappingURL` в JS.

    Сторонние пакеты иногда ссылаются в JS на несуществующие .map-файлы
    (например, drf-yasg 1.21.17: redoc-old/redoc.min.js → redoc.min.map),
    и тогда collectstatic падает. Source map нужны только в DevTools,
    поэтому для JS ссылки оставляем как есть; CSS обрабатывается штатно.
    """

    patterns = tuple(
        (ext, rules) for ext, rules in CompressedManifestStaticFilesStorage.patterns if ext != "*.js"
    )
