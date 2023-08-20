server {
    server_name io.livecode.ch;
    listen 80;
    location /static {
      alias /home/namin/io.livecode.ch/pub/static;
    }
    location / {
        include proxy_params;
        proxy_read_timeout 600s;
        proxy_connect_timeout 600s;
        proxy_pass http://unix:/home/namin/io.livecode.ch/pub/iolive.sock;
    }

}