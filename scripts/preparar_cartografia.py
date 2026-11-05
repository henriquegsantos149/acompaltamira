"""Prepara cartografia local rastreável; nenhuma geometria de infraestrutura é estimada.

Executar da raiz: python codex/scripts/preparar_cartografia.py
Dependências: requests, pymupdf, numpy, pillow, shapely, pyproj, rasterio.
"""
from pathlib import Path
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
import os

# Não usar proj.db de PostGIS herdado no ambiente com wheels GDAL/PROJ atuais.
for variable in ('PROJ_LIB', 'PROJ_DATA', 'GDAL_DATA'):
    os.environ.pop(variable, None)

import fitz
import numpy as np
from PIL import Image, ImageDraw
from pyproj import Transformer, Geod
import requests
import rasterio
from rasterio.transform import Affine, array_bounds
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import shape, mapping, Point
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[2]
GIS = ROOT / 'codex/dados/geoespaciais'
ORIG = GIS / 'originais'
OUT = GIS / 'processados'
REVIEW = ROOT / 'codex/verificacao/dashboard/cartografia'
PDF = ROOT / 'documentos/PMISB-ALTAMIRA-APROVADO.pdf'
NOW = datetime.now(timezone.utc).isoformat()
for folder in (ORIG, OUT, REVIEW):
    folder.mkdir(parents=True, exist_ok=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def download(name, url):
    path = ORIG / name
    if not path.exists():
        response = requests.get(url, timeout=90)
        response.raise_for_status()
        path.write_bytes(response.content)
    return path


def fit_axis(pixels, coordinates):
    matrix = np.column_stack([pixels, np.ones(len(pixels))])
    slope, intercept = np.linalg.lstsq(matrix, coordinates, rcond=None)[0]
    residuals = np.asarray(coordinates) - (slope * np.asarray(pixels) + intercept)
    return slope, intercept, residuals.tolist()


def prepare_raster(doc, spec):
    """Ajuste apenas aos rótulos/tiques impressos; não aprova posição absoluta."""
    name = spec['id']
    source = ORIG / (name + '.png')
    source.write_bytes(doc.extract_image(spec['xref'])['image'])
    image = Image.open(source).convert('RGB')
    a, c, rx = fit_axis(spec['pixels_x'], spec['world_x'])
    e, f, ry = fit_axis(spec['pixels_y'], spec['world_y'])
    full_transform = Affine(a, 0, c, 0, e, f)
    x0, y0, x1, y1 = spec['crop']
    pixels = np.asarray(image.crop((x0, y0, x1, y1)))
    src_transform = full_transform * Affine.translation(x0, y0)
    h, w = pixels.shape[:2]
    tif = REVIEW / (name + '.tif')
    with rasterio.open(tif, 'w', driver='GTiff', height=h, width=w, count=3,
                       dtype='uint8', crs=spec['crs'], transform=src_transform,
                       compress='deflate') as dst:
        dst.write(pixels.transpose(2, 0, 1))
    dst_transform, dw, dh = calculate_default_transform(
        spec['crs'], 'EPSG:4326', w, h, *array_bounds(h, w, src_transform))
    rgba = np.zeros((4, dh, dw), dtype=np.uint8)
    for band in range(3):
        reproject(pixels[:, :, band], rgba[band], src_transform=src_transform,
                  src_crs=spec['crs'], dst_transform=dst_transform,
                  dst_crs='EPSG:4326', resampling=Resampling.bilinear)
    reproject(np.full((h, w), 255, dtype=np.uint8), rgba[3],
              src_transform=src_transform, src_crs=spec['crs'],
              dst_transform=dst_transform, dst_crs='EPSG:4326',
              resampling=Resampling.nearest)
    png = REVIEW / (name + '_wgs84.png')
    Image.fromarray(rgba.transpose(1, 2, 0)).save(png)
    west, south, east, north = array_bounds(dh, dw, dst_transform)
    debug = image.copy()
    draw = ImageDraw.Draw(debug)
    for px in spec['pixels_x']:
        draw.line([(px, y0), (px, y1)], fill='magenta', width=2)
    for py in spec['pixels_y']:
        draw.line([(x0, py), (x1, py)], fill='magenta', width=2)
    debug.save(REVIEW / (name + '_controle.png'))
    # Barra gráfica é um teste independente de escala, mas pertence à mesma fonte.
    if spec['crs'] == 'EPSG:4674':
        geod = Geod(ellps='GRS80')
        pixel_m = abs(geod.inv(c, -3.2, c + a, -3.2)[2])
        residual_m = [abs(v) * 111000 for v in rx + ry]
    else:
        pixel_m = abs(a)
        residual_m = [abs(v) for v in rx + ry]
    bar_m = spec['bar_pixels'] * pixel_m
    assert abs(bar_m - 2000) / 2000 < .015
    assert max(residual_m) < pixel_m * 1.1
    assert -53 < west < east < -51 and -4 < south < north < -2
    report = dict(spec, prepared_at=NOW, source_sha256=sha(source),
                  pdf_sha256=sha(PDF), affine_full=list(full_transform)[:6],
                  affine_crop=list(src_transform)[:6], residual_x=rx, residual_y=ry,
                  residual_unit='graus' if spec['crs'] == 'EPSG:4674' else 'metros',
                  residual_max_m_approx=max(residual_m), pixel_m_approx=pixel_m,
                  scale_bar_computed_m=bar_m, bounds=[[south, west], [north, east]],
                  output_sha256=sha(png), status='pendente',
                  reason='Ajuste interno e barra gráfica coerentes; falta validação absoluta contra base independente. Não liberada como sobreposição no catálogo.',
                  method='Leitura visual dos tiques/cruzetas (fig36) ou centros dos rótulos de moldura (fig53), mínimos quadrados separados X/Y, recorte nativo, reprojeção rasterio para WGS84; sem vetorização.')
    save(REVIEW / (name + '_georef.json'), report)
    return report


def main():
    api = 'https://servicodados.ibge.gov.br/api/v3/malhas/municipios/1500602'
    source_url = api + '?formato=application/vnd.geo%2Bjson&qualidade=maxima&periodo=2022'
    original = download('ibge_altamira_2022.geojson', source_url)
    meta = download('ibge_metadados_2022.json', api + '/metadados?periodo=2022')
    locality = download('ibge_localidade.json', 'https://servicodados.ibge.gov.br/api/v1/localidades/municipios/1500602')
    districts = download('ibge_distritos.json', 'https://servicodados.ibge.gov.br/api/v1/localidades/municipios/1500602/distritos')
    download('ibge_api_documentacao.html', 'https://servicodados.ibge.gov.br/api/docs/malhas?versao=3')
    download('ibge_informacoes_tecnicas_2022.pdf', 'https://biblioteca.ibge.gov.br/visualizacao/livros/liv101998.pdf')
    assert json.loads(locality.read_text(encoding='utf-8'))['nome'] == 'Altamira'
    raw = json.loads(original.read_text(encoding='utf-8'))
    assert len(raw['features']) == 1
    feature = raw['features'][0]
    assert str(feature['properties']['codarea']) == '1500602'
    geom = shape(feature['geometry'])
    assert geom.is_valid and not geom.is_empty and geom.geom_type in ('Polygon', 'MultiPolygon')
    transformer = Transformer.from_crs('EPSG:4674', 'EPSG:4326', always_xy=True)
    transformed = transform(transformer.transform, geom)
    west, south, east, north = transformed.bounds
    assert -56 < west < east < -51 and -10 < south < north < -2
    assert transformed.contains(Point(-52.21, -3.20))
    area_km2 = abs(Geod(ellps='WGS84').geometry_area_perimeter(transformed)[0]) / 1e6
    published_area = float(json.loads(meta.read_text())[0]['area']['dimensao'])
    assert abs(area_km2 - published_area) / published_area < .02
    feature['geometry'] = mapping(transformed)
    feature['properties'].update(id='municipio-1500602', nome='Altamira', ano=2022,
                                 origem='IBGE / API Malhas v3', source_url=source_url,
                                 source_sha256=sha(original), natureza='contexto oficial; malha simplificada')
    save(OUT / 'limite_altamira_ibge.geojson', raw)
    metadata = dict(id='limite-altamira-ibge', source_url=source_url, source_sha256=sha(original),
                    prepared_at=NOW, year=2022, source_crs='EPSG:4674 (SIRGAS2000), conforme documentação da malha IBGE; a resposta GeoJSON não contém membro crs',
                    display_crs='EPSG:4326', axis_order='longitude, latitude',
                    transformation=transformer.description, transformation_accuracy_m=transformer.accuracy,
                    method='API oficial simplificada, qualidade maxima; pyproj always_xy=True; nenhuma edição topológica ou simplificação adicional',
                    scale='Malha de origem 1:250.000; API simplificada não conserva garantia dessa escala para medição',
                    license='Atribuição IBGE; documentação oficial da malha preservada; nenhuma licença adicional presumida',
                    responsible='Preparação automatizada Codex; responsável técnico não informado',
                    bounds=[[south, west], [north, east]], feature_count=1,
                    original_area_km2=published_area, geodesic_area_km2=area_km2,
                    output_sha256=sha(OUT / 'limite_altamira_ibge.geojson'),
                    warning='Contexto territorial de 2022, não substitui levantamento cadastral ou limites das unidades do PMISB. Tentativa de período 2024 retornou HTTP500 e foi preservada.')
    save(OUT / 'limite_altamira_ibge_metadados.json', metadata)
    doc = fitz.open(PDF)
    reports = [prepare_raster(doc, spec) for spec in [
        dict(id='figura36', page=106, xref=967, crs='EPSG:31982',
             pixels_x=[200, 552.5, 905, 1257.5], world_x=[362000,364000,366000,368000],
             pixels_y=[116,469,821,1174,1526], world_y=[9650000,9648000,9646000,9644000,9642000],
             crop=[41,33,1380,1668], bar_pixels=353, printed_scale='1:50.000'),
        dict(id='figura53', page=124, xref=1052, crs='EPSG:4674',
             pixels_x=[144,410,677,943,1209], world_x=[-(52+v/60) for v in [15,14,13,12,11]],
             pixels_y=[170,438,705,973,1241,1508], world_y=[-(3+v/60) for v in [10,11,12,13,14,15]],
             crop=[41,43,1299,1436], bar_pixels=288, printed_scale='1:60.000'),
    ]]
    text = doc[117].get_text()
    (ORIG / 'tabela20_p118.txt').write_text(text, encoding='utf-8')
    start = text.index('Parque Ipê')
    stop = text.index('Fonte: PMA, 2022.')
    blocks = re.split(r'(E [\d.]+,00 m, N [\d.]+,00 m)', text[start:stop])
    candidates = []
    for index in range(0, len(blocks)-1, 2):
        labels = [s.strip() for s in blocks[index].splitlines() if s.strip()]
        easting, northing = re.findall(r'[\d.]+,00', blocks[index+1])
        name = labels[0]
        candidates.append(dict(id=f'microssistema-{len(candidates)+1:02}', nome=name,
                               zona=labels[1], localizacao_reservatorio=' '.join(labels[2:]) or None,
                               e=float(easting.replace('.','').replace(',','.')),
                               n=float(northing.replace('.','').replace(',','.')),
                               src_textual='UTM 22S', datum=None, epsg=None, geometry=None,
                               source='/api/documento#page=118', source_page=118, source_table=20,
                               source_sha256=sha(PDF), year=2022, status='pendente',
                               reason='Datum não informado na tabela20.' + (' E262642 preservado; divergência de faixa exige conferência da fonte.' if name == 'Parque Ipê' else '')))
    assert len(candidates) == 10 and candidates[0]['e'] == 262642
    save(OUT / 'microssistemas_candidatos.json', {'records': candidates})
    save(OUT / 'distritos_cadastro_ibge.json', {'source': 'https://servicodados.ibge.gov.br/api/v1/localidades/municipios/1500602/distritos',
         'source_sha256': sha(districts), 'retrieved_at': NOW, 'year': None,
         'records': [dict(id=v['id'], nome=v['nome'], geometry=None, status='pendente',
                          reason='Nome e código confirmados pela API Localidades. Sem geometria: API Malhas v3 não fornece subdivisão distrital neste endpoint; não equivale às unidades históricas PMISB.')
                     for v in json.loads(districts.read_text(encoding='utf-8'))]})
    layers = [dict(id='limite-altamira-ibge', title='Limite municipal de Altamira — IBGE 2022', status='validada', type='geojson',
                   url='/geo/limite_altamira_ibge.geojson', bounds=metadata['bounds'], source=source_url, year=2022,
                   description='Contexto oficial simplificado da API IBGE, sem uso cadastral ou medição de engenharia.', feature_count=1)]
    inventory = list(csv.DictReader((ROOT / 'codex/planejamento/INVENTARIO_CARTOGRAFICO.csv').open(encoding='utf-8-sig'), delimiter=';'))
    pages = [24,186,23,118,106,94,98,114,124,125,126,127,154,59,239,270]
    for i, row in enumerate(inventory[1:], 1):
        reason = row['condicao_publicacao']
        if i in (4,8):
            reason = next(r['reason'] for r in reports if r['page'] == pages[i])
        layers.append(dict(id=f'pmisb-cadastro-{i:02}', title=row['camada_candidata'], status='pendente', type='document',
                           url=f'/api/documento#page={pages[i]}', source='PMISB Altamira — documento aprovado',
                           source_page=pages[i], year=2022, description=row['referencia'] + '. ' + row['estado_atual'],
                           reason=reason))
    save(OUT / 'catalogo.json', {'layers': layers})
    manifest = {str(p.relative_to(GIS)): sha(p) for p in sorted(ORIG.iterdir()) if p.is_file()}
    save(GIS / 'manifesto_fontes.json', {'prepared_at': NOW, 'pdf':str(PDF.relative_to(ROOT)), 'pdf_sha256':sha(PDF), 'sha256':manifest})
    checks = dict(status='passou', municipal_feature_count=1, municipal_geometry_valid=True,
                  municipal_bounds=metadata['bounds'], area_difference_pct=abs(area_km2-published_area)/published_area*100,
                  ibge_code='1500602', candidates_without_geometry=len(candidates), catalog_layers=len(layers),
                  raster_internal_checks_passed=2, rasters_published=0, pending_absolute_validation=2,
                  tested_at=NOW, transformer=transformer.description,
                  tests=['ID oficial e nome Altamira', 'SHA256 de originais e derivados', 'geometria válida e não vazia',
                         'bounds plausíveis e sede dentro do limite', 'área geodésica até2% da área IBGE',
                         'ordem longitude/latitude explícita', 'GCP/resíduos e barra até1,5%',
                         '10 registros tabela20 sem datum/EPSG/geometria', 'Parque Ipê E262642 preservado'])
    save(REVIEW / 'verificacao_gis.json', checks)
    print(json.dumps(checks, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
