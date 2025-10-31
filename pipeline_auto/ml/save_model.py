#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para salvar o modelo de detecção de fraude
"""

import pandas as pd
import numpy as np
import pickle
import joblib
from datetime import datetime
import os
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import RidgeClassifier
import json

def main():
    print("="*80)
    print("SALVANDO MODELO DE DETECCAO DE FRAUDE")
    print("="*80)
    
    # Carregar dados
    print("Carregando dados...")
    df = pd.read_csv('../data/script_7_grafo/dataset_final_com_grafo.csv')
    print(f"Dataset carregado: {df.shape}")
    
    # Definir features
    features_preco = [
        'preco_atual', 'preco_sugerido_hp', 'diferenca_preco_perc',
        'flag_preco_muito_baixo', 'flag_preco_medio_baixo', 'flag_preco_ligeiramente_baixo'
    ]
    
    features_ignorar = [
        'id_anuncio', 'seller_id', 'catalog_product_id', 'titulo', 'link_anuncio',
        'imagem_url_principal', 'descricao', 'vendedor_nome', 'power_seller_status',
        'reputation_level', 'distribuicao_estrelas', 'conexoes_vendedores_alt',
        'score_de_suspeita', 'usado_seminovo'
    ]
    
    # Features a usar
    features_to_use = [col for col in df.columns if col not in features_ignorar + features_preco + ['is_fraud_suspect_v2']]
    print(f"Features selecionadas: {len(features_to_use)}")
    
    # Preparar dados
    print("\nPreparando dados...")
    X = df[features_to_use].copy()
    y = df['is_fraud_suspect_v2']
    
    # Tratar colunas categóricas
    categorical_columns = X.select_dtypes(include=['object', 'category']).columns.tolist()
    label_encoders = {}
    
    for col in categorical_columns:
        try:
            le = LabelEncoder()
            X[col] = X[col].astype(str).fillna('unknown')
            X[col] = le.fit_transform(X[col])
            label_encoders[col] = le
            print(f"   OK {col}: {len(le.classes_)} categorias")
        except Exception as e:
            print(f"   ERRO {col}: {str(e)}")
            X[col] = X[col].astype(str).apply(lambda x: hash(x) % 1000)
    
    X = X.fillna(0)
    
    # Normalizar features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Treinar modelo
    print("   Treinando modelo RidgeClassifier...")
    model = RidgeClassifier(random_state=42)
    model.fit(X_scaled, y)
    
    # Criar diretório para modelos
    model_dir = "../models"
    os.makedirs(model_dir, exist_ok=True)
    
    # Timestamp para versionamento
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Criar pipeline completo
    pipeline_info = {
        'model': model,
        'scaler': scaler,
        'label_encoders': label_encoders,
        'features_to_use': features_to_use,
        'features_ignorar': features_ignorar,
        'features_preco': features_preco,
        'categorical_columns': categorical_columns,
        'target_variable': 'is_fraud_suspect_v2',
        'model_type': 'RidgeClassifier',
        'training_date': datetime.now().isoformat(),
        'dataset_shape': df.shape,
        'n_features': len(features_to_use)
    }
    
    # Salvar usando joblib
    model_filename = f"fraud_detection_model_{timestamp}.joblib"
    model_path = os.path.join(model_dir, model_filename)
    
    print(f"\nSalvando modelo em: {model_path}")
    joblib.dump(pipeline_info, model_path)
    
    # Salvar backup com pickle
    pickle_filename = f"fraud_detection_model_{timestamp}.pkl"
    pickle_path = os.path.join(model_dir, pickle_filename)
    
    print(f"Salvando backup em: {pickle_path}")
    with open(pickle_path, 'wb') as f:
        pickle.dump(pipeline_info, f)
    
    # Salvar metadados
    metadata = {
        'model_name': 'Fraud Detection RidgeClassifier',
        'version': timestamp,
        'model_type': 'RidgeClassifier',
        'features_count': len(features_to_use),
        'training_samples': len(df),
        'target_distribution': {
            'fraud_suspects': int(df['is_fraud_suspect_v2'].sum()),
            'legitimate': int((df['is_fraud_suspect_v2'] == 0).sum()),
            'fraud_rate': float(df['is_fraud_suspect_v2'].mean())
        },
        'feature_categories': {
            'grafo_features': len([f for f in features_to_use if 'grafo' in f.lower()]),
            'embedding_features': len([f for f in features_to_use if 'embedding' in f.lower()]),
            'review_features': len([f for f in features_to_use if 'review' in f.lower() or 'sentimento' in f.lower()]),
            'vendedor_features': len([f for f in features_to_use if 'vendedor' in f.lower()]),
            'imagem_features': len([f for f in features_to_use if 'imagem' in f.lower() or 'reuso' in f.lower()])
        }
    }
    
    metadata_path = os.path.join(model_dir, f"model_metadata_{timestamp}.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"Metadados salvos em: {metadata_path}")
    
    # Criar script de carregamento
    script_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para carregar e usar o modelo de detecção de fraude
Modelo treinado em: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

import joblib
import pandas as pd
import numpy as np

class FraudDetectionModel:
    def __init__(self, model_path):
        """Carrega o modelo e pipeline de preprocessamento"""
        self.pipeline = joblib.load(model_path)
        self.model = self.pipeline['model']
        self.scaler = self.pipeline['scaler']
        self.label_encoders = self.pipeline['label_encoders']
        self.features_to_use = self.pipeline['features_to_use']
        self.categorical_columns = self.pipeline['categorical_columns']
        
    def preprocess_data(self, df):
        """Preprocessa os dados para predição"""
        # Selecionar features
        X = df[self.features_to_use].copy()
        
        # Tratar colunas categóricas
        for col in self.categorical_columns:
            if col in X.columns:
                try:
                    le = self.label_encoders[col]
                    X[col] = X[col].astype(str).fillna('unknown')
                    # Para novos valores não vistos no treino
                    X[col] = X[col].apply(lambda x: x if x in le.classes_ else 'unknown')
                    X[col] = le.transform(X[col])
                except Exception as e:
                    # Se falhar, usar hash
                    X[col] = X[col].astype(str).apply(lambda x: hash(x) % 1000)
        
        # Preencher valores faltantes
        X = X.fillna(0)
        
        # Normalizar
        X_scaled = self.scaler.transform(X)
        
        return X_scaled
    
    def predict(self, df):
        """Faz predições em um DataFrame"""
        X_scaled = self.preprocess_data(df)
        
        # Gerar scores usando decision_function
        scores = self.model.decision_function(X_scaled)
        ml_scores = 1 / (1 + np.exp(-scores))  # Sigmoid para 0-1
        
        # Predições binárias
        predictions = (ml_scores > 0.5).astype(int)
        
        return ml_scores, predictions
    
    def predict_single(self, data_dict):
        """Faz predição em um único produto"""
        df = pd.DataFrame([data_dict])
        return self.predict(df)

# Exemplo de uso
if __name__ == "__main__":
    # Carregar modelo
    model = FraudDetectionModel("{model_path}")
    
    # Exemplo de predição
    print("Modelo carregado com sucesso!")
    print(f"Features esperadas: {{len(model.features_to_use)}}")
    print(f"Tipo do modelo: {{model.model.__class__.__name__}}")
'''
    
    script_path = os.path.join(model_dir, f"load_fraud_model_{timestamp}.py")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"Script de carregamento salvo em: {script_path}")
    
    # Resumo final
    print(f"\nMODELO SALVO COM SUCESSO!")
    print(f"   - Modelo principal: {model_path}")
    print(f"   - Backup: {pickle_path}")
    print(f"   - Metadados: {metadata_path}")
    print(f"   - Script de uso: {script_path}")
    
    print(f"\nINFORMACOES DO MODELO:")
    print(f"   - Tipo: RidgeClassifier")
    print(f"   - Features: {len(features_to_use)}")
    print(f"   - Amostras de treino: {len(df)}")
    print(f"   - Taxa de fraude: {df['is_fraud_suspect_v2'].mean():.1%}")
    
    print(f"\nCOMO USAR O MODELO:")
    print(f"   from load_fraud_model_{timestamp} import FraudDetectionModel")
    print(f"   model = FraudDetectionModel('{model_path}')")
    print(f"   ml_scores, predictions = model.predict(df)")

if __name__ == "__main__":
    main()
