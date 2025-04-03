#!/bin/bash

# Lista de arquivos a serem processados
files=(
  "templates/buscar-cpf.html"
  "templates/verificar-cpf.html"
  "templates/payment.html"
  "templates/payment_update.html"
  "templates/sms_config.html"
  "templates/thank_you.html"
  "templates/unauthorized.html"
)

# O script UTM Handler para adicionar
utm_script='<!-- Script UTM Handler -->
<script 
        src="https://d1atmqbt05kisf.cloudfront.net/scripts/utm-handler.js"
        data-token="03e84f3d-5678-4a63-8c78-eb4459e13467"
        data-click-id-param="click_id">
</script>'

# Processar cada arquivo
for file in "${files[@]}"; do
  echo "Processando $file..."
  
  # Verificar se o arquivo já contém o script
  if grep -q "d1atmqbt05kisf.cloudfront.net/scripts/utm-handler.js" "$file"; then
    echo "  Arquivo já contém o script UTM Handler. Pulando."
    continue
  fi
  
  # Verificar se o arquivo contém {% include 'shared_resources.html' %}
  if grep -q "{% include 'shared_resources.html' %}" "$file"; then
    echo "  Arquivo inclui shared_resources.html. Pulando."
    continue
  fi
  
  # Fazer backup do arquivo original
  cp "$file" "${file}.bak"
  
  # Adicionar o script após a tag <head>
  sed -i '/<head>/a\'$'\n'"$utm_script" "$file"
  
  echo "  Script UTM Handler adicionado com sucesso!"
done

echo "Processo concluído!"