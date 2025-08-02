# -*- coding: utf-8 -*-
# src/evaluation/visualize_results.py

import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# Import conditionnel des bibliotheques de visualisation
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class VisualizationConfig:
    """Configuration pour la visualisation"""
    figure_size: Tuple[int, int] = (12, 8)
    color_palette: str = "viridis"
    style: str = "whitegrid"
    save_format: str = "png"
    dpi: int = 300
    show_plots: bool = True

class TranslationResultsVisualizer:
    """Visualisateur de resultats d'evaluation de traduction"""
    
    def __init__(self, config: VisualizationConfig = None):
        """
        Initialise le visualisateur
        
        Args:
            config: Configuration de visualisation
        """
        self.config = config or VisualizationConfig()
        
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Matplotlib non disponible, certaines visualisations seront indisponibles")
        
        if SEABORN_AVAILABLE:
            sns.set_style(self.config.style)
            sns.set_palette(self.config.color_palette)
        
        # Configuration matplotlib
        if MATPLOTLIB_AVAILABLE:
            plt.rcParams['figure.figsize'] = self.config.figure_size
            plt.rcParams['font.size'] = 10
            plt.rcParams['axes.labelsize'] = 12
            plt.rcParams['axes.titlesize'] = 14
            plt.rcParams['legend.fontsize'] = 10
            plt.rcParams['xtick.labelsize'] = 10
            plt.rcParams['ytick.labelsize'] = 10
    
    def visualize_metric_comparison(self, results: Dict[str, Any], 
                                  output_file: Optional[str] = None) -> bool:
        """
        Visualise la comparaison des metriques
        
        Args:
            results: Resultats d'evaluation
            output_file: Fichier de sortie (optionnel)
        
        Returns:
            True si visualisation reussie
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.error("Matplotlib requis pour la visualisation")
            return False
        
        try:
            scores = results.get('scores', {})
            if not scores:
                logger.warning("Aucun score trouve dans les resultats")
                return False
            
            # Preparer les donnees
            metrics = list(scores.keys())
            values = [scores[metric] for metric in metrics]
            
            # Creer le graphique
            fig, ax = plt.subplots(figsize=self.config.figure_size)
            
            # Graphique en barres
            bars = ax.bar(metrics, values, alpha=0.7)
            
            # Colorer les barres selon les scores
            for bar, value in zip(bars, values):
                if value >= 0.8:
                    bar.set_color('green')
                elif value >= 0.6:
                    bar.set_color('orange')
                else:
                    bar.set_color('red')
            
            # Configuration du graphique
            ax.set_ylabel('Score')
            ax.set_title('Comparaison des Metriques d\'Evaluation')
            ax.set_ylim(0, 1)
            
            # Ajouter les valeurs sur les barres
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f'{value:.3f}', ha='center', va='bottom')
            
            # Legende
            green_patch = mpatches.Patch(color='green', label='Excellent (e0.8)')
            orange_patch = mpatches.Patch(color='orange', label='Bon (e0.6)')
            red_patch = mpatches.Patch(color='red', label='Faible (<0.6)')
            ax.legend(handles=[green_patch, orange_patch, red_patch])
            
            plt.tight_layout()
            
            # Sauvegarder si demande
            if output_file:
                plt.savefig(output_file, dpi=self.config.dpi, format=self.config.save_format)
                logger.info(f"Graphique sauvegarde: {output_file}")
            
            if self.config.show_plots:
                plt.show()
            
            plt.close()
            return True
            
        except Exception as e:
            logger.error(f"Erreur visualisation metriques: {e}")
            return False
    
    def visualize_score_distribution(self, results: Dict[str, Any], 
                                   output_file: Optional[str] = None) -> bool:
        """
        Visualise la distribution des scores individuels
        
        Args:
            results: Resultats d'evaluation avec scores individuels
            output_file: Fichier de sortie (optionnel)
        
        Returns:
            True si visualisation reussie
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.error("Matplotlib requis pour la visualisation")
            return False
        
        individual_scores = results.get('individual', [])
        if not individual_scores:
            logger.warning("Aucun score individuel trouve")
            return False
        
        try:
            # Extraire les scores par metrique
            metrics = list(individual_scores[0]['scores'].keys())
            metric_scores = {metric: [] for metric in metrics}
            
            for item in individual_scores:
                for metric in metrics:
                    metric_scores[metric].append(item['scores'][metric])
            
            # Creer le graphique
            fig, axes = plt.subplots(1, len(metrics), figsize=(4*len(metrics), 6))
            if len(metrics) == 1:
                axes = [axes]
            
            for i, metric in enumerate(metrics):
                scores = metric_scores[metric]
                
                # Histogramme
                axes[i].hist(scores, bins=20, alpha=0.7, color=f'C{i}')
                axes[i].set_xlabel('Score')
                axes[i].set_ylabel('Frequence')
                axes[i].set_title(f'Distribution {metric.upper()}')
                axes[i].axvline(np.mean(scores), color='red', linestyle='--', 
                              label=f'Moyenne: {np.mean(scores):.3f}')
                axes[i].legend()
            
            plt.tight_layout()
            
            # Sauvegarder si demande
            if output_file:
                plt.savefig(output_file, dpi=self.config.dpi, format=self.config.save_format)
                logger.info(f"Graphique sauvegarde: {output_file}")
            
            if self.config.show_plots:
                plt.show()
            
            plt.close()
            return True
            
        except Exception as e:
            logger.error(f"Erreur visualisation distribution: {e}")
            return False
    
    def visualize_segment_analysis(self, results: Dict[str, Any], 
                                 output_file: Optional[str] = None,
                                 top_n: int = 10) -> bool:
        """
        Visualise l'analyse des segments (meilleurs et pires)
        
        Args:
            results: Resultats d'evaluation avec scores individuels
            output_file: Fichier de sortie (optionnel)
            top_n: Nombre de segments a afficher
        
        Returns:
            True si visualisation reussie
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.error("Matplotlib requis pour la visualisation")
            return False
        
        individual_scores = results.get('individual', [])
        if not individual_scores:
            logger.warning("Aucun score individuel trouve")
            return False
        
        try:
            # Calculer score moyen par segment
            segment_scores = []
            for i, item in enumerate(individual_scores):
                scores = list(item['scores'].values())
                avg_score = sum(scores) / len(scores)
                segment_scores.append({
                    'index': i,
                    'score': avg_score,
                    'reference': item['reference'][:50] + "..." if len(item['reference']) > 50 else item['reference'],
                    'candidate': item['candidate'][:50] + "..." if len(item['candidate']) > 50 else item['candidate']
                })
            
            # Trier par score
            segment_scores.sort(key=lambda x: x['score'])
            
            # Selectionner les meilleurs et pires
            worst_segments = segment_scores[:top_n]
            best_segments = segment_scores[-top_n:]
            
            # Creer le graphique
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(self.config.figure_size[0], self.config.figure_size[1]*1.5))
            
            # Pires segments
            worst_scores = [seg['score'] for seg in worst_segments]
            worst_labels = [f"Seg {seg['index']}" for seg in worst_segments]
            
            bars1 = ax1.barh(worst_labels, worst_scores, color='red', alpha=0.7)
            ax1.set_xlabel('Score')
            ax1.set_title(f'Top {top_n} des Pires Segments')
            ax1.set_xlim(0, 1)
            
            # Ajouter les valeurs
            for bar, score in zip(bars1, worst_scores):
                width = bar.get_width()
                ax1.text(width + 0.01, bar.get_y() + bar.get_height()/2, 
                        f'{score:.3f}', ha='left', va='center')
            
            # Meilleurs segments
            best_scores = [seg['score'] for seg in best_segments]
            best_labels = [f"Seg {seg['index']}" for seg in best_segments]
            
            bars2 = ax2.barh(best_labels, best_scores, color='green', alpha=0.7)
            ax2.set_xlabel('Score')
            ax2.set_title(f'Top {top_n} des Meilleurs Segments')
            ax2.set_xlim(0, 1)
            
            # Ajouter les valeurs
            for bar, score in zip(bars2, best_scores):
                width = bar.get_width()
                ax2.text(width + 0.01, bar.get_y() + bar.get_height()/2, 
                        f'{score:.3f}', ha='left', va='center')
            
            plt.tight_layout()
            
            # Sauvegarder si demande
            if output_file:
                plt.savefig(output_file, dpi=self.config.dpi, format=self.config.save_format)
                logger.info(f"Graphique sauvegarde: {output_file}")
            
            if self.config.show_plots:
                plt.show()
            
            plt.close()
            return True
            
        except Exception as e:
            logger.error(f"Erreur visualisation segments: {e}")
            return False
    
    def visualize_custom_metrics_breakdown(self, results: Dict[str, Any], 
                                         output_file: Optional[str] = None) -> bool:
        """
        Visualise la decomposition des metriques personnalisees
        
        Args:
            results: Resultats avec metriques personnalisees
            output_file: Fichier de sortie (optionnel)
        
        Returns:
            True si visualisation reussie
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.error("Matplotlib requis pour la visualisation")
            return False
        
        # Verifier si on a des metriques personnalisees
        breakdown = results.get('breakdown', {})
        if not breakdown:
            logger.warning("Aucune decomposition de metriques personnalisees trouvee")
            return False
        
        try:
            # Preparer les donnees
            categories = list(breakdown.keys())
            values = list(breakdown.values())
            
            # Creer le graphique radar
            angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
            values += values[:1]  # Fermer le polygone
            angles += angles[:1]
            
            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
            
            # Dessiner le polygone
            ax.plot(angles, values, 'o-', linewidth=2, label='Scores')
            ax.fill(angles, values, alpha=0.25)
            
            # Configuration
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels([cat.replace('_', ' ').title() for cat in categories])
            ax.set_ylim(0, 1)
            ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
            ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'])
            ax.grid(True)
            
            # Titre
            ax.set_title('Decomposition des Metriques Personnalisees', 
                        size=16, y=1.1)
            
            # Ajouter les valeurs
            for angle, value, category in zip(angles[:-1], values[:-1], categories):
                ax.text(angle, value + 0.05, f'{value:.3f}', 
                       horizontalalignment='center', verticalalignment='center')
            
            plt.tight_layout()
            
            # Sauvegarder si demande
            if output_file:
                plt.savefig(output_file, dpi=self.config.dpi, format=self.config.save_format)
                logger.info(f"Graphique sauvegarde: {output_file}")
            
            if self.config.show_plots:
                plt.show()
            
            plt.close()
            return True
            
        except Exception as e:
            logger.error(f"Erreur visualisation metriques personnalisees: {e}")
            return False
    
    def create_evaluation_report(self, results: Dict[str, Any], 
                               output_dir: str = "evaluation_reports") -> bool:
        """
        Cree un rapport complet d'evaluation avec visualisations
        
        Args:
            results: Resultats d'evaluation
            output_dir: Repertoire de sortie
        
        Returns:
            True si rapport cree avec succes
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generer les visualisations
            visualizations_created = []
            
            # 1. Comparaison des metriques
            if self.visualize_metric_comparison(results, 
                                              str(output_path / "metric_comparison.png")):
                visualizations_created.append("metric_comparison.png")
            
            # 2. Distribution des scores (si disponible)
            if 'individual' in results:
                if self.visualize_score_distribution(results, 
                                                   str(output_path / "score_distribution.png")):
                    visualizations_created.append("score_distribution.png")
                
                if self.visualize_segment_analysis(results, 
                                                 str(output_path / "segment_analysis.png")):
                    visualizations_created.append("segment_analysis.png")
            
            # 3. Metriques personnalisees (si disponible)
            if 'breakdown' in results:
                if self.visualize_custom_metrics_breakdown(results, 
                                                         str(output_path / "custom_metrics.png")):
                    visualizations_created.append("custom_metrics.png")
            
            # 4. Creer le rapport HTML
            html_report = self._generate_html_report(results, visualizations_created)
            
            with open(output_path / "evaluation_report.html", 'w', encoding='utf-8') as f:
                f.write(html_report)
            
            # 5. Sauvegarder les resultats JSON
            with open(output_path / "evaluation_results.json", 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Rapport d'evaluation complet cree dans: {output_path}")
            logger.info(f"Visualisations creees: {len(visualizations_created)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur creation rapport: {e}")
            return False
    
    def _generate_html_report(self, results: Dict[str, Any], 
                            visualizations: List[str]) -> str:
        """
        Genere un rapport HTML
        
        Args:
            results: Resultats d'evaluation
            visualizations: Liste des fichiers de visualisation
        
        Returns:
            Code HTML du rapport
        """
        html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport d'Evaluation - WikiTranslateAI</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .score-high {{ color: #28a745; font-weight: bold; }}
        .score-medium {{ color: #ffc107; font-weight: bold; }}
        .score-low {{ color: #dc3545; font-weight: bold; }}
        .metrics-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .metrics-table th, .metrics-table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        .metrics-table th {{
            background-color: #f2f2f2;
        }}
        .visualization {{
            text-align: center;
            margin: 20px 0;
        }}
        .visualization img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .summary-box {{
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>=Ê Rapport d'Evaluation - WikiTranslateAI</h1>
        
        <div class="summary-box">
            <h2>=Ë Resume</h2>
            <p><strong>Segments evalues:</strong> {results.get('segment_count', 'N/A')}</p>
            {self._format_article_info(results)}
        </div>
        
        <h2>=È Scores des Metriques</h2>
        <table class="metrics-table">
            <thead>
                <tr>
                    <th>Metrique</th>
                    <th>Score</th>
                    <th>Evaluation</th>
                </tr>
            </thead>
            <tbody>
                {self._format_scores_table(results.get('scores', {}))}
            </tbody>
        </table>
        
        {self._format_custom_metrics(results)}
        
        <h2>=Ê Visualisations</h2>
        {self._format_visualizations(visualizations)}
        
        <div class="summary-box">
            <h2>=¡ Interpretation</h2>
            <p>Les metriques d'evaluation fournissent une vue d'ensemble de la qualite de traduction:</p>
            <ul>
                <li><strong>BLEU:</strong> Mesure la precision des n-grammes</li>
                <li><strong>METEOR:</strong> Prend en compte la synonymie et l'ordre des mots</li>
                <li><strong>Preservation Culturelle:</strong> Specifique aux langues africaines</li>
                <li><strong>Coherence Semantique:</strong> Fluidite et logique du texte</li>
            </ul>
        </div>
        
        <hr>
        <p><em>Rapport genere par WikiTranslateAI - {self._get_timestamp()}</em></p>
    </div>
</body>
</html>
        """
        return html
    
    def _format_article_info(self, results: Dict[str, Any]) -> str:
        """Formate les informations d'article"""
        if 'article' in results:
            article = results['article']
            return f"""
            <p><strong>Article:</strong> {article.get('title', 'N/A')}</p>
            <p><strong>Langues:</strong> {article.get('source_language', 'N/A')}  {article.get('target_language', 'N/A')}</p>
            """
        return ""
    
    def _format_scores_table(self, scores: Dict[str, float]) -> str:
        """Formate le tableau des scores"""
        rows = []
        for metric, score in scores.items():
            if score is None:
                score_class = "score-low"
                evaluation = "Erreur"
                score_text = "N/A"
            elif score >= 0.8:
                score_class = "score-high"
                evaluation = "Excellent"
                score_text = f"{score:.3f}"
            elif score >= 0.6:
                score_class = "score-medium"
                evaluation = "Bon"
                score_text = f"{score:.3f}"
            else:
                score_class = "score-low"
                evaluation = "Faible"
                score_text = f"{score:.3f}"
            
            rows.append(f"""
                <tr>
                    <td>{metric.upper()}</td>
                    <td class="{score_class}">{score_text}</td>
                    <td>{evaluation}</td>
                </tr>
            """)
        
        return "".join(rows)
    
    def _format_custom_metrics(self, results: Dict[str, Any]) -> str:
        """Formate les metriques personnalisees"""
        if 'breakdown' not in results:
            return ""
        
        breakdown = results['breakdown']
        rows = []
        for metric, score in breakdown.items():
            metric_name = metric.replace('_', ' ').title()
            if score >= 0.8:
                score_class = "score-high"
            elif score >= 0.6:
                score_class = "score-medium"
            else:
                score_class = "score-low"
            
            rows.append(f"""
                <tr>
                    <td>{metric_name}</td>
                    <td class="{score_class}">{score:.3f}</td>
                </tr>
            """)
        
        table = f"""
        <h2><¯ Metriques Personnalisees</h2>
        <table class="metrics-table">
            <thead>
                <tr>
                    <th>Metrique</th>
                    <th>Score</th>
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>
        """
        return table
    
    def _format_visualizations(self, visualizations: List[str]) -> str:
        """Formate les visualisations"""
        if not visualizations:
            return "<p>Aucune visualisation disponible (matplotlib requis)</p>"
        
        viz_html = []
        for viz in visualizations:
            viz_name = viz.replace('_', ' ').replace('.png', '').title()
            viz_html.append(f"""
                <div class="visualization">
                    <h3>{viz_name}</h3>
                    <img src="{viz}" alt="{viz_name}">
                </div>
            """)
        
        return "".join(viz_html)
    
    def _get_timestamp(self) -> str:
        """Retourne le timestamp actuel"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Fonction utilitaire pour visualisation rapide
def quick_visualize(results_file: str, output_dir: str = "visualization_output") -> bool:
    """
    Visualisation rapide depuis un fichier de resultats
    
    Args:
        results_file: Fichier JSON des resultats
        output_dir: Repertoire de sortie
    
    Returns:
        True si succes
    """
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        visualizer = TranslationResultsVisualizer()
        return visualizer.create_evaluation_report(results, output_dir)
        
    except Exception as e:
        logger.error(f"Erreur visualisation rapide: {e}")
        return False

if __name__ == "__main__":
    # Test du visualisateur
    test_results = {
        "segment_count": 10,
        "scores": {
            "bleu": 0.75,
            "meteor": 0.68,
            "custom": 0.82
        },
        "breakdown": {
            "cultural_preservation": 0.85,
            "semantic_coherence": 0.72,
            "fluency_reformulation": 0.79
        },
        "individual": [
            {
                "reference": "Le vodun est une religion importante.",
                "candidate": "Vodun religion importante est.",
                "scores": {"bleu": 0.6, "meteor": 0.7, "custom": 0.8}
            },
            {
                "reference": "Les rois du Dahomey etaient puissants.",
                "candidate": "Dahomey kings were powerful.",
                "scores": {"bleu": 0.4, "meteor": 0.5, "custom": 0.3}
            }
        ]
    }
    
    if MATPLOTLIB_AVAILABLE:
        visualizer = TranslationResultsVisualizer()
        success = visualizer.create_evaluation_report(test_results, "test_report")
        if success:
            print(" Rapport de test cree avec succes dans 'test_report/'")
        else:
            print("L Erreur lors de la creation du rapport")
    else:
        print("L Matplotlib non disponible pour les tests de visualisation")
        print("Installation: pip install matplotlib seaborn")