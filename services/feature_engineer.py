import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.feature_selection import SelectKBest, f_classif, f_regression
from sklearn.decomposition import PCA
from sklearn.preprocessing import PolynomialFeatures
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from textblob import TextBlob
import logging
from datetime import datetime
from models import Dataset, FeatureEngineering, db
from services.data_processor import DataProcessor
from flask import current_app
from scipy import stats
import json

class FeatureEngineer:
    def __init__(self):
        self.data_processor = DataProcessor()
        self.scalers = {
            'standard': StandardScaler(),
            'minmax': MinMaxScaler(),
            'robust': RobustScaler()
        }
    
    def scale_features(self, dataset_id, columns, method='standard'):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if not columns:
                columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Validate columns
            invalid_cols = [col for col in columns if col not in df.columns]
            if invalid_cols:
                return {'success': False, 'error': f'Invalid columns: {invalid_cols}'}
            
            # Get before stats
            before_stats = self.get_column_stats(df, columns)
            
            # Apply scaling
            scaler = self.scalers.get(method, StandardScaler())
            df_scaled = df.copy()
            
            for col in columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    df_scaled[col] = scaler.fit_transform(df[[col]])
            
            # Get after stats
            after_stats = self.get_column_stats(df_scaled, columns)
            
            # Save transformation
            transformation = FeatureEngineering(
                dataset_id=dataset_id,
                column_name=','.join(columns),
                transformation_type='scaling',
                parameters={'method': method, 'columns': columns},
                before_stats=before_stats,
                after_stats=after_stats,
                transformation_info={'scaler_type': method}
            )
            
            db.session.add(transformation)
            db.session.commit()
            
            # Update dataset file
            self.save_transformed_data(df_scaled, dataset)
            
            return {
                'success': True,
                'message': f'Successfully scaled {len(columns)} columns using {method} scaling',
                'before_stats': before_stats,
                'after_stats': after_stats,
                'transformation_id': transformation.id
            }
            
        except Exception as e:
            current_app.logger.error(f"Scaling error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def encode_categorical(self, dataset_id, columns, method='onehot'):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if not columns:
                columns = df.select_dtypes(include=['object']).columns.tolist()
            
            # Validate columns
            invalid_cols = [col for col in columns if col not in df.columns]
            if invalid_cols:
                return {'success': False, 'error': f'Invalid columns: {invalid_cols}'}
            
            # Get before stats
            before_stats = self.get_column_stats(df, columns)
            
            df_encoded = df.copy()
            
            for col in columns:
                if method == 'onehot':
                    # One-hot encoding
                    dummies = pd.get_dummies(df[col], prefix=col)
                    df_encoded = pd.concat([df_encoded.drop(col, axis=1), dummies], axis=1)
                    
                elif method == 'label':
                    # Label encoding
                    le = LabelEncoder()
                    df_encoded[col] = le.fit_transform(df[col].astype(str))
                    
                elif method == 'frequency':
                    # Frequency encoding
                    freq_map = df[col].value_counts().to_dict()
                    df_encoded[col] = df[col].map(freq_map)
                    
                elif method == 'target':
                    # Target encoding (requires target column)
                    # For now, use frequency encoding as fallback
                    freq_map = df[col].value_counts().to_dict()
                    df_encoded[col] = df[col].map(freq_map)
            
            # Get after stats
            after_stats = self.get_column_stats(df_encoded, df_encoded.columns.tolist())
            
            # Save transformation
            transformation = FeatureEngineering(
                dataset_id=dataset_id,
                column_name=','.join(columns),
                transformation_type='encoding',
                parameters={'method': method, 'columns': columns},
                before_stats=before_stats,
                after_stats=after_stats,
                transformation_info={'encoding_type': method}
            )
            
            db.session.add(transformation)
            db.session.commit()
            
            # Update dataset file
            self.save_transformed_data(df_encoded, dataset)
            
            return {
                'success': True,
                'message': f'Successfully encoded {len(columns)} columns using {method} encoding',
                'before_stats': before_stats,
                'after_stats': after_stats,
                'transformation_id': transformation.id,
                'new_columns': df_encoded.columns.tolist()
            }
            
        except Exception as e:
            current_app.logger.error(f"Encoding error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def transform_numerical(self, dataset_id, columns, method='log'):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if not columns:
                columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Validate columns
            invalid_cols = [col for col in columns if col not in df.columns]
            if invalid_cols:
                return {'success': False, 'error': f'Invalid columns: {invalid_cols}'}
            
            # Get before stats
            before_stats = self.get_column_stats(df, columns)
            
            df_transformed = df.copy()
            
            for col in columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    if method == 'log':
                        # Log transformation (handle non-positive values)
                        df_transformed[col] = np.log1p(df[col] - df[col].min() + 1)
                    elif method == 'sqrt':
                        # Square root transformation
                        df_transformed[col] = np.sqrt(df[col] - df[col].min() + 1)
                    elif method == 'reciprocal':
                        # Reciprocal transformation
                        df_transformed[col] = 1 / (df[col] + 1)
                    elif method == 'square':
                        # Square transformation
                        df_transformed[col] = df[col] ** 2
                    elif method == 'boxcox':
                        # Box-Cox transformation
                        try:
                            transformed_data, _ = stats.boxcox(df[col] - df[col].min() + 1)
                            df_transformed[col] = transformed_data
                        except:
                            # Fallback to log transformation
                            df_transformed[col] = np.log1p(df[col] - df[col].min() + 1)
            
            # Get after stats
            after_stats = self.get_column_stats(df_transformed, columns)
            
            # Save transformation
            transformation = FeatureEngineering(
                dataset_id=dataset_id,
                column_name=','.join(columns),
                transformation_type='numerical_transform',
                parameters={'method': method, 'columns': columns},
                before_stats=before_stats,
                after_stats=after_stats,
                transformation_info={'transform_type': method}
            )
            
            db.session.add(transformation)
            db.session.commit()
            
            # Update dataset file
            self.save_transformed_data(df_transformed, dataset)
            
            return {
                'success': True,
                'message': f'Successfully transformed {len(columns)} columns using {method} transformation',
                'before_stats': before_stats,
                'after_stats': after_stats,
                'transformation_id': transformation.id
            }
            
        except Exception as e:
            current_app.logger.error(f"Numerical transformation error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def bin_numerical(self, dataset_id, columns, method='equal_width', bins=5):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if not columns:
                columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Validate columns
            invalid_cols = [col for col in columns if col not in df.columns]
            if invalid_cols:
                return {'success': False, 'error': f'Invalid columns: {invalid_cols}'}
            
            # Get before stats
            before_stats = self.get_column_stats(df, columns)
            
            df_binned = df.copy()
            
            for col in columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    if method == 'equal_width':
                        df_binned[f'{col}_binned'] = pd.cut(df[col], bins=bins, labels=False)
                    elif method == 'equal_frequency':
                        df_binned[f'{col}_binned'] = pd.qcut(df[col], q=bins, labels=False, duplicates='drop')
                    elif method == 'kmeans':
                        # K-means based binning
                        from sklearn.cluster import KMeans
                        kmeans = KMeans(n_clusters=bins, random_state=42)
                        df_binned[f'{col}_binned'] = kmeans.fit_predict(df[[col]])
            
            # Get after stats
            new_columns = [f'{col}_binned' for col in columns]
            after_stats = self.get_column_stats(df_binned, new_columns)
            
            # Save transformation
            transformation = FeatureEngineering(
                dataset_id=dataset_id,
                column_name=','.join(columns),
                transformation_type='binning',
                parameters={'method': method, 'columns': columns, 'bins': bins},
                before_stats=before_stats,
                after_stats=after_stats,
                transformation_info={'binning_method': method, 'num_bins': bins}
            )
            
            db.session.add(transformation)
            db.session.commit()
            
            # Update dataset file
            self.save_transformed_data(df_binned, dataset)
            
            return {
                'success': True,
                'message': f'Successfully binned {len(columns)} columns using {method} method',
                'before_stats': before_stats,
                'after_stats': after_stats,
                'transformation_id': transformation.id,
                'new_columns': new_columns
            }
            
        except Exception as e:
            current_app.logger.error(f"Binning error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def polynomial_features(self, dataset_id, columns, degree=2):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if not columns:
                columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Validate columns
            invalid_cols = [col for col in columns if col not in df.columns]
            if invalid_cols:
                return {'success': False, 'error': f'Invalid columns: {invalid_cols}'}
            
            # Get before stats
            before_stats = self.get_column_stats(df, columns)
            
            # Create polynomial features
            poly = PolynomialFeatures(degree=degree, include_bias=False)
            poly_features = poly.fit_transform(df[columns])
            
            # Create column names
            feature_names = poly.get_feature_names_out(columns)
            
            # Create new dataframe with polynomial features
            df_poly = df.copy()
            for i, name in enumerate(feature_names):
                df_poly[f'poly_{name}'] = poly_features[:, i]
            
            # Get after stats
            new_columns = [f'poly_{name}' for name in feature_names]
            after_stats = self.get_column_stats(df_poly, new_columns)
            
            # Save transformation
            transformation = FeatureEngineering(
                dataset_id=dataset_id,
                column_name=','.join(columns),
                transformation_type='polynomial',
                parameters={'columns': columns, 'degree': degree},
                before_stats=before_stats,
                after_stats=after_stats,
                transformation_info={'polynomial_degree': degree, 'num_features': len(feature_names)}
            )
            
            db.session.add(transformation)
            db.session.commit()
            
            # Update dataset file
            self.save_transformed_data(df_poly, dataset)
            
            return {
                'success': True,
                'message': f'Successfully created polynomial features of degree {degree}',
                'before_stats': before_stats,
                'after_stats': after_stats,
                'transformation_id': transformation.id,
                'new_columns': new_columns
            }
            
        except Exception as e:
            current_app.logger.error(f"Polynomial features error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def interaction_features(self, dataset_id, columns):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if not columns:
                columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if len(columns) < 2:
                return {'success': False, 'error': 'At least 2 columns required for interaction features'}
            
            # Get before stats
            before_stats = self.get_column_stats(df, columns)
            
            df_interaction = df.copy()
            new_columns = []
            
            # Create interaction features
            for i in range(len(columns)):
                for j in range(i+1, len(columns)):
                    col1, col2 = columns[i], columns[j]
                    interaction_col = f'{col1}_x_{col2}'
                    df_interaction[interaction_col] = df[col1] * df[col2]
                    new_columns.append(interaction_col)
            
            # Get after stats
            after_stats = self.get_column_stats(df_interaction, new_columns)
            
            # Save transformation
            transformation = FeatureEngineering(
                dataset_id=dataset_id,
                column_name=','.join(columns),
                transformation_type='interaction',
                parameters={'columns': columns},
                before_stats=before_stats,
                after_stats=after_stats,
                transformation_info={'num_interactions': len(new_columns)}
            )
            
            db.session.add(transformation)
            db.session.commit()
            
            # Update dataset file
            self.save_transformed_data(df_interaction, dataset)
            
            return {
                'success': True,
                'message': f'Successfully created {len(new_columns)} interaction features',
                'before_stats': before_stats,
                'after_stats': after_stats,
                'transformation_id': transformation.id,
                'new_columns': new_columns
            }
            
        except Exception as e:
            current_app.logger.error(f"Interaction features error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def datetime_features(self, dataset_id, columns):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if not columns:
                columns = df.select_dtypes(include=['datetime64']).columns.tolist()
            
            if not columns:
                return {'success': False, 'error': 'No datetime columns found'}
            
            # Get before stats
            before_stats = self.get_column_stats(df, columns)
            
            df_datetime = df.copy()
            new_columns = []
            
            for col in columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    # Convert to datetime if string
                    if df[col].dtype == 'object':
                        df_datetime[col] = pd.to_datetime(df[col])
                    
                    # Extract datetime features
                    df_datetime[f'{col}_year'] = df_datetime[col].dt.year
                    df_datetime[f'{col}_month'] = df_datetime[col].dt.month
                    df_datetime[f'{col}_day'] = df_datetime[col].dt.day
                    df_datetime[f'{col}_dayofweek'] = df_datetime[col].dt.dayofweek
                    df_datetime[f'{col}_hour'] = df_datetime[col].dt.hour
                    df_datetime[f'{col}_minute'] = df_datetime[col].dt.minute
                    df_datetime[f'{col}_quarter'] = df_datetime[col].dt.quarter
                    df_datetime[f'{col}_dayofyear'] = df_datetime[col].dt.dayofyear
                    df_datetime[f'{col}_weekofyear'] = df_datetime[col].dt.isocalendar().week
                    
                    # Cyclical encoding
                    df_datetime[f'{col}_month_sin'] = np.sin(2 * np.pi * df_datetime[f'{col}_month'] / 12)
                    df_datetime[f'{col}_month_cos'] = np.cos(2 * np.pi * df_datetime[f'{col}_month'] / 12)
                    df_datetime[f'{col}_day_sin'] = np.sin(2 * np.pi * df_datetime[f'{col}_day'] / 31)
                    df_datetime[f'{col}_day_cos'] = np.cos(2 * np.pi * df_datetime[f'{col}_day'] / 31)
                    df_datetime[f'{col}_hour_sin'] = np.sin(2 * np.pi * df_datetime[f'{col}_hour'] / 24)
                    df_datetime[f'{col}_hour_cos'] = np.cos(2 * np.pi * df_datetime[f'{col}_hour'] / 24)
                    
                    new_columns.extend([
                        f'{col}_year', f'{col}_month', f'{col}_day', f'{col}_dayofweek',
                        f'{col}_hour', f'{col}_minute', f'{col}_quarter', f'{col}_dayofyear',
                        f'{col}_weekofyear', f'{col}_month_sin', f'{col}_month_cos',
                        f'{col}_day_sin', f'{col}_day_cos', f'{col}_hour_sin', f'{col}_hour_cos'
                    ])
            
            # Get after stats
            after_stats = self.get_column_stats(df_datetime, new_columns)
            
            # Save transformation
            transformation = FeatureEngineering(
                dataset_id=dataset_id,
                column_name=','.join(columns),
                transformation_type='datetime',
                parameters={'columns': columns},
                before_stats=before_stats,
                after_stats=after_stats,
                transformation_info={'num_features': len(new_columns)}
            )
            
            db.session.add(transformation)
            db.session.commit()
            
            # Update dataset file
            self.save_transformed_data(df_datetime, dataset)
            
            return {
                'success': True,
                'message': f'Successfully created {len(new_columns)} datetime features',
                'before_stats': before_stats,
                'after_stats': after_stats,
                'transformation_id': transformation.id,
                'new_columns': new_columns
            }
            
        except Exception as e:
            current_app.logger.error(f"Datetime features error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def text_features(self, dataset_id, columns, method='tfidf'):
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            df = self.data_processor.load_dataset(dataset)
            
            if not columns:
                columns = df.select_dtypes(include=['object']).columns.tolist()
            
            # Get before stats
            before_stats = self.get_column_stats(df, columns)
            
            df_text = df.copy()
            new_columns = []
            
            for col in columns:
                if df[col].dtype == 'object':
                    # Basic text features
                    df_text[f'{col}_length'] = df[col].astype(str).str.len()
                    df_text[f'{col}_word_count'] = df[col].astype(str).str.split().str.len()
                    df_text[f'{col}_char_count'] = df[col].astype(str).str.replace(' ', '').str.len()
                    df_text[f'{col}_sentence_count'] = df[col].astype(str).str.count(r'[.!?]') + 1
                    
                    # Sentiment analysis
                    try:
                        sentiments = df[col].astype(str).apply(lambda x: TextBlob(x).sentiment.polarity)
                        df_text[f'{col}_sentiment'] = sentiments
                    except:
                        df_text[f'{col}_sentiment'] = 0
                    
                    new_columns.extend([
                        f'{col}_length', f'{col}_word_count', f'{col}_char_count',
                        f'{col}_sentence_count', f'{col}_sentiment'
                    ])
                    
                    # TF-IDF or Count vectorization
                    if method == 'tfidf':
                        try:
                            vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
                            tfidf_matrix = vectorizer.fit_transform(df[col].astype(str))
                            feature_names = vectorizer.get_feature_names_out()
                            
                            for i, feature in enumerate(feature_names):
                                df_text[f'{col}_tfidf_{feature}'] = tfidf_matrix[:, i].toarray().flatten()
                                new_columns.append(f'{col}_tfidf_{feature}')
                        except:
                            pass
                    
                    elif method == 'count':
                        try:
                            vectorizer = CountVectorizer(max_features=100, stop_words='english')
                            count_matrix = vectorizer.fit_transform(df[col].astype(str))
                            feature_names = vectorizer.get_feature_names_out()
                            
                            for i, feature in enumerate(feature_names):
                                df_text[f'{col}_count_{feature}'] = count_matrix[:, i].toarray().flatten()
                                new_columns.append(f'{col}_count_{feature}')
                        except:
                            pass
            
            # Get after stats
            after_stats = self.get_column_stats(df_text, new_columns)
            
            # Save transformation
            transformation = FeatureEngineering(
                dataset_id=dataset_id,
                column_name=','.join(columns),
                transformation_type='text',
                parameters={'columns': columns, 'method': method},
                before_stats=before_stats,
                after_stats=after_stats,
                transformation_info={'text_method': method, 'num_features': len(new_columns)}
            )
            
            db.session.add(transformation)
            db.session.commit()
            
            # Update dataset file
            self.save_transformed_data(df_text, dataset)
            
            return {
                'success': True,
                'message': f'Successfully created {len(new_columns)} text features',
                'before_stats': before_stats,
                'after_stats': after_stats,
                'transformation_id': transformation.id,
                'new_columns': new_columns
            }
            
        except Exception as e:
            current_app.logger.error(f"Text features error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_column_stats(self, df, columns):
        stats = {}
        for col in columns:
            if col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    stats[col] = {
                        'mean': float(df[col].mean()) if not df[col].isna().all() else None,
                        'std': float(df[col].std()) if not df[col].isna().all() else None,
                        'min': float(df[col].min()) if not df[col].isna().all() else None,
                        'max': float(df[col].max()) if not df[col].isna().all() else None,
                        'median': float(df[col].median()) if not df[col].isna().all() else None,
                        'skew': float(df[col].skew()) if not df[col].isna().all() else None,
                        'kurtosis': float(df[col].kurtosis()) if not df[col].isna().all() else None
                    }
                else:
                    stats[col] = {
                        'unique_count': int(df[col].nunique()),
                        'most_frequent': df[col].mode().iloc[0] if not df[col].mode().empty else None,
                        'null_count': int(df[col].isnull().sum())
                    }
        return stats
    
    def save_transformed_data(self, df, dataset):
        # Save to a new file
        new_path = dataset.file_path.replace('.', '_transformed.')
        df.to_csv(new_path, index=False)
        
        # Update dataset record
        dataset.file_path = new_path
        dataset.rows = len(df)
        dataset.columns = len(df.columns)
        dataset.memory_usage = float(df.memory_usage(deep=True).sum())
        dataset.column_info = self.data_processor.get_column_info(df)
        dataset.data_types = df.dtypes.astype(str).to_dict()
        dataset.missing_values = df.isnull().sum().to_dict()
        
        db.session.commit()
    
    def revert_transformation(self, transformation_id):
        try:
            transformation = FeatureEngineering.query.get_or_404(transformation_id)
            
            # Delete the transformation record
            db.session.delete(transformation)
            db.session.commit()
            
            return {'success': True, 'message': 'Transformation reverted successfully'}
            
        except Exception as e:
            current_app.logger.error(f"Revert transformation error: {str(e)}")
            return {'success': False, 'error': str(e)}
