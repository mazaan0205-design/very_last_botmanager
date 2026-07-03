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

# 4. Copy your frontend Laravel contents into the container
COPY frontend/ .

# 5. Install Composer tool natively
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# 6. Run dependency installation
RUN composer install --no-dev --optimize-autoloader --no-interaction --no-scripts

# 7. Create the empty SQLite database file
RUN touch database/database.sqlite

# 8. Set proper application permissions
RUN chown -R www-data:www-data /var/www/html/storage /var/www/html/bootstrap/cache /var/www/html/database

EXPOSE 80

# 9. Run migrations automatically on startup, then start Apache
CMD php artisan migrate --force && apache2-foreground