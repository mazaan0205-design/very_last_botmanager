FROM php:8.2-apache

# 1. Install required system tools and PHP extensions for Laravel
RUN apt-get update && apt-get install -y \
    libpng-dev libjpeg-dev libfreetype6-dev zip unzip git libbrotli-dev \
    && docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install pdo_mysql gd

# 2. Turn on Apache rewrite mode for Laravel routing paths
RUN a2enmod rewrite

# 3. Point Apache's web folder strictly to Laravel's public directory
ENV APACHE_DOCUMENT_ROOT /var/www/html/public
RUN sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/sites-available/*.conf
RUN sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf

WORKDIR /var/www/html
COPY . .

# 4. Automatically intercept local URLs and rewrite them to your live Render backend
RUN find . -type f -not -path '*/.*' -exec sed -i 's|127.0.0.1:8001|very-last-botmanager.onrender.com|g' {} + \
    && find . -type f -not -path '*/.*' -exec sed -i 's|localhost:8001|very-last-botmanager.onrender.com|g' {} + \
    && find . -type f -not -path '*/.*' -exec sed -i 's|http://very-last-botmanager.onrender.com|https://very-last-botmanager.onrender.com|g' {} +

# 5. Install Composer tool natively
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# 6. Run dependency installation (skipping custom post-install scripts)
RUN composer install --no-dev --optimize-autoloader --no-interaction --no-scripts

# 7. Create the empty SQLite database file during build time
RUN mkdir -p /opt/render/project/src/database && touch /opt/render/project/src/database/database.sqlite

# 8. Explicitly create missing Laravel system storage and bootstrap folders
RUN mkdir -p storage/framework/cache/data \
             storage/framework/sessions \
             storage/framework/views \
             storage/logs \
             bootstrap/cache

# 9. Set proper application permissions securely
RUN chown -R www-data:www-data /var/www/html/storage /var/www/html/bootstrap/cache /opt/render/project/src/database

EXPOSE 80

# 10. Force absolute SQLite path, clear cache, run migrations, and start Apache web server
CMD ["sh", "-c", "mkdir -p /opt/render/project/src/database && touch /opt/render/project/src/database/database.sqlite && DB_DATABASE=/opt/render/project/src/database/database.sqlite php artisan config:clear && DB_DATABASE=/opt/render/project/src/database/database.sqlite php artisan cache:clear && DB_DATABASE=/opt/render/project/src/database/database.sqlite php artisan migrate --force && DB_DATABASE=/opt/render/project/src/database/database.sqlite apache2-foreground"]
