from flask import Blueprint, request, jsonify, session
from services.feature_engineer import FeatureEngineer
from app import db
from models import Dataset, Feature
import logging

feature_engineer_bp = Blueprint('feature_engineer', __name__, url_prefix='/api/feature')

@feature_engineer_bp.route('/datasets', methods=['GET'])
def get_datasets():
    """Get all available datasets for analysis operations"""
    try:
        # Query all datasets from the database
        datasets = Dataset.query.all()
        dataset_list = []

        # Iterate through each dataset and format the data for JSON response
        for dataset in datasets:
            dataset_list.append({
                'id': dataset.id,
                'filename': dataset.filename,
                'rows': dataset.num_rows,
                'columns': dataset.num_columns,
                'file_size': dataset.file_size,
                # Safely format the upload timestamp:
                # If dataset.created_at is None, assign None. Otherwise, call isoformat().
                'created_at': dataset.upload_timestamp.isoformat() if dataset.upload_timestamp else None
            })

        # Return a successful JSON response with the list of datasets
        return jsonify({
            'success': True,
            'datasets': dataset_list
        })

    except Exception as e:
        # Log the error on the server side for debugging
        logging.error(f"Error fetching datasets: {str(e)}")
        # Return a JSON response indicating failure and the error message, with a 500 status code
        return jsonify({'success': False, 'error': f"An internal server error occurred while retrieving datasets: {str(e)}"}), 500

@feature_engineer_bp.route('/scale', methods=['POST'])
def apply_scaling():
    """Apply scaling transformation to a feature"""
    try:
        dataset_id = request.json.get('dataset_id')
        feature = request.json.get('feature')
        method = request.json.get('method', 'standard')
        
        if not dataset_id or not feature or not method:
            return jsonify({'success': False, 'error': 'Dataset ID, feature, and method are required'}), 400
        
        dataset = Dataset.query.get_or_404(dataset_id)
        engineer = FeatureEngineer()
        
        result = engineer.apply_scaling(dataset.file_path, feature, method)
        
        return jsonify({
            'success': True,
            'feature_name': result.get('feature_name'),
            'message': f'Applied {method} scaling to {feature}'
        })
        
    except Exception as e:
        logging.error(f"Scaling error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feature_engineer_bp.route('/encode', methods=['POST'])
def apply_encoding():
    """Apply encoding transformation to a feature"""
    try:
        dataset_id = request.json.get('dataset_id')
        feature = request.json.get('feature')
        method = request.json.get('method', 'label')
        
        if not dataset_id or not feature or not method:
            return jsonify({'success': False, 'error': 'Dataset ID, feature, and method are required'}), 400
        
        dataset = Dataset.query.get_or_404(dataset_id)
        engineer = FeatureEngineer()
        
        result = engineer.apply_encoding(dataset.file_path, feature, method)
        
        if method == 'one_hot':
            return jsonify({
                'success': True,
                'features': result.get('features', []),
                'message': f'Applied {method} encoding to {feature}'
            })
        else:
            return jsonify({
                'success': True,
                'feature_name': result.get('feature_name'),
                'message': f'Applied {method} encoding to {feature}'
            })
        
    except Exception as e:
        logging.error(f"Encoding error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feature_engineer_bp.route('/bin', methods=['POST'])
def apply_binning():
    """Apply binning transformation to a feature"""
    try:
        dataset_id = request.json.get('dataset_id')
        feature = request.json.get('feature')
        bins = request.json.get('bins', 5)
        method = request.json.get('method', 'equal_width')
        
        if not dataset_id or not feature:
            return jsonify({'success': False, 'error': 'Dataset ID and feature are required'}), 400
        
        dataset = Dataset.query.get_or_404(dataset_id)
        engineer = FeatureEngineer()
        
        result = engineer.apply_binning(dataset.file_path, feature, bins, method)
        
        return jsonify({
            'success': True,
            'feature_name': result.get('feature_name'),
            'message': f'Applied binning to {feature} with {bins} bins'
        })
        
    except Exception as e:
        logging.error(f"Binning error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feature_engineer_bp.route('/transform', methods=['POST'])
def apply_transformation():
    """Apply mathematical transformation to a feature"""
    try:
        dataset_id = request.json.get('dataset_id')
        feature = request.json.get('feature')
        method = request.json.get('method', 'log')
        
        if not dataset_id or not feature or not method:
            return jsonify({'success': False, 'error': 'Dataset ID, feature, and method are required'}), 400
        
        dataset = Dataset.query.get_or_404(dataset_id)
        engineer = FeatureEngineer()
        
        result = engineer.apply_transformation(dataset.file_path, feature, method)
        
        return jsonify({
            'success': True,
            'feature_name': result.get('feature_name'),
            'message': f'Applied {method} transformation to {feature}'
        })
        
    except Exception as e:
        logging.error(f"Transformation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feature_engineer_bp.route('/impute', methods=['POST'])
def handle_missing_values():
    """Handle missing values in a feature"""
    try:
        dataset_id = request.json.get('dataset_id')
        feature = request.json.get('feature')
        strategy = request.json.get('strategy', 'mean')
        
        if not dataset_id or not feature or not strategy:
            return jsonify({'success': False, 'error': 'Dataset ID, feature, and strategy are required'}), 400
        
        dataset = Dataset.query.get_or_404(dataset_id)
        engineer = FeatureEngineer()
        
        result = engineer.handle_missing_values(dataset.file_path, feature, strategy)
        
        return jsonify({
            'success': True,
            'feature_name': result.get('feature_name'),
            'message': f'Applied {strategy} imputation to {feature}'
        })
        
    except Exception as e:
        logging.error(f"Imputation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feature_engineer_bp.route('/create', methods=['POST'])
def create_feature():
    """Create new feature from arithmetic operations"""
    try:
        dataset_id = request.json.get('dataset_id')
        feature1 = request.json.get('feature1')
        feature2 = request.json.get('feature2')
        operation = request.json.get('operation')
        
        if not dataset_id or not feature1 or not feature2 or not operation:
            return jsonify({'success': False, 'error': 'Dataset ID, both features, and operation are required'}), 400
        
        dataset = Dataset.query.get_or_404(dataset_id)
        engineer = FeatureEngineer()
        
        result = engineer.create_arithmetic_feature(dataset.file_path, feature1, feature2, operation)
        
        return jsonify({
            'success': True,
            'feature_name': result.get('feature_name'),
            'message': f'Created feature from {feature1} {operation} {feature2}'
        })
        
    except Exception as e:
        logging.error(f"Feature creation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feature_engineer_bp.route('/scale/<int:dataset_id>', methods=['POST'])
def scale_features(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        engineer = FeatureEngineer()
        
        columns = request.json.get('columns', [])
        method = request.json.get('method', 'standard')
        
        if not columns:
            return jsonify({'error': 'Columns parameter is required'}), 400
        
        result = engineer.scale_features(dataset.file_path, columns, method)
        
        if result['success']:
            # Save feature transformations to database
            for col in columns:
                feature = Feature(
                    dataset_id=dataset_id,
                    feature_name=f"{col}_scaled",
                    original_name=col,
                    feature_type='numerical',
                    transformation_type='scaling',
                    transformation_params={'method': method}
                )
                db.session.add(feature)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'result': result['result'],
                'stats': result['stats']
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Feature scaling error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@feature_engineer_bp.route('/encode/<int:dataset_id>', methods=['POST'])
def encode_features(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        engineer = FeatureEngineer()
        
        columns = request.json.get('columns', [])
        method = request.json.get('method', 'onehot')
        
        if not columns:
            return jsonify({'error': 'Columns parameter is required'}), 400
        
        result = engineer.encode_categorical_features(dataset.file_path, columns, method)
        
        if result['success']:
            # Save feature transformations to database
            for col in columns:
                feature = Feature(
                    dataset_id=dataset_id,
                    feature_name=f"{col}_encoded",
                    original_name=col,
                    feature_type='categorical',
                    transformation_type='encoding',
                    transformation_params={'method': method}
                )
                db.session.add(feature)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'result': result['result'],
                'stats': result['stats']
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Feature encoding error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@feature_engineer_bp.route('/binning/<int:dataset_id>', methods=['POST'])
def bin_features(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        engineer = FeatureEngineer()
        
        columns = request.json.get('columns', [])
        method = request.json.get('method', 'equal_width')
        bins = request.json.get('bins', 5)
        
        if not columns:
            return jsonify({'error': 'Columns parameter is required'}), 400
        
        result = engineer.bin_numerical_features(dataset.file_path, columns, method, bins)
        
        if result['success']:
            # Save feature transformations to database
            for col in columns:
                feature = Feature(
                    dataset_id=dataset_id,
                    feature_name=f"{col}_binned",
                    original_name=col,
                    feature_type='categorical',
                    transformation_type='binning',
                    transformation_params={'method': method, 'bins': bins}
                )
                db.session.add(feature)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'result': result['result'],
                'stats': result['stats']
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Feature binning error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@feature_engineer_bp.route('/transform/<int:dataset_id>', methods=['POST'])
def transform_features(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        engineer = FeatureEngineer()
        
        columns = request.json.get('columns', [])
        method = request.json.get('method', 'log')
        
        if not columns:
            return jsonify({'error': 'Columns parameter is required'}), 400
        
        result = engineer.transform_numerical_features(dataset.file_path, columns, method)
        
        if result['success']:
            # Save feature transformations to database
            for col in columns:
                feature = Feature(
                    dataset_id=dataset_id,
                    feature_name=f"{col}_{method}",
                    original_name=col,
                    feature_type='numerical',
                    transformation_type='transformation',
                    transformation_params={'method': method}
                )
                db.session.add(feature)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'result': result['result'],
                'stats': result['stats']
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Feature transformation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@feature_engineer_bp.route('/polynomial/<int:dataset_id>', methods=['POST'])
def polynomial_features(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        engineer = FeatureEngineer()
        
        columns = request.json.get('columns', [])
        degree = request.json.get('degree', 2)
        
        if not columns:
            return jsonify({'error': 'Columns parameter is required'}), 400
        
        result = engineer.create_polynomial_features(dataset.file_path, columns, degree)
        
        if result['success']:
            return jsonify({
                'success': True,
                'result': result['result'],
                'new_features': result['new_features']
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Polynomial features error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@feature_engineer_bp.route('/datetime/<int:dataset_id>', methods=['POST'])
def datetime_features(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        engineer = FeatureEngineer()
        
        columns = request.json.get('columns', [])
        features = request.json.get('features', ['year', 'month', 'day'])
        
        if not columns:
            return jsonify({'error': 'Columns parameter is required'}), 400
        
        result = engineer.extract_datetime_features(dataset.file_path, columns, features)
        
        if result['success']:
            return jsonify({
                'success': True,
                'result': result['result'],
                'new_features': result['new_features']
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"DateTime features error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@feature_engineer_bp.route('/text/<int:dataset_id>', methods=['POST'])
def text_features(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        engineer = FeatureEngineer()
        
        columns = request.json.get('columns', [])
        method = request.json.get('method', 'basic')
        
        if not columns:
            return jsonify({'error': 'Columns parameter is required'}), 400
        
        result = engineer.extract_text_features(dataset.file_path, columns, method)
        
        if result['success']:
            return jsonify({
                'success': True,
                'result': result['result'],
                'new_features': result['new_features']
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Text features error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@feature_engineer_bp.route('/interactions/<int:dataset_id>', methods=['POST'])
def feature_interactions(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        engineer = FeatureEngineer()
        
        columns = request.json.get('columns', [])
        method = request.json.get('method', 'multiply')
        
        if len(columns) < 2:
            return jsonify({'error': 'At least 2 columns are required for interactions'}), 400
        
        result = engineer.create_feature_interactions(dataset.file_path, columns, method)
        
        if result['success']:
            return jsonify({
                'success': True,
                'result': result['result'],
                'new_features': result['new_features']
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Feature interactions error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@feature_engineer_bp.route('/list/<int:dataset_id>')
def list_features(dataset_id):
    try:
        features = Feature.query.filter_by(dataset_id=dataset_id).all()
        
        feature_list = []
        for feature in features:
            feature_list.append({
                'id': feature.id,
                'name': feature.feature_name,
                'original_name': feature.original_name,
                'type': feature.feature_type,
                'transformation': feature.transformation_type,
                'params': feature.transformation_params,
                'is_target': feature.is_target,
                'is_selected': feature.is_selected,
                'importance': feature.importance_score
            })
        
        return jsonify({
            'success': True,
            'features': feature_list
        })
        
    except Exception as e:
        logging.error(f"List features error: {str(e)}")
        return jsonify({'error': str(e)}), 500
