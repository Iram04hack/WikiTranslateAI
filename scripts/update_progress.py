#!/usr/bin/env python3
"""
Script pour mettre à jour la progression du projet WikiTranslateAI
Usage: python scripts/update_progress.py --step 1_1_1 --status completed
"""

import json
import argparse
from datetime import datetime
from pathlib import Path

def load_progress():
    """Charge le fichier de progression"""
    progress_file = Path(__file__).parent.parent / "PROGRESS_TRACKER.json"
    with open(progress_file, 'r') as f:
        return json.load(f)

def save_progress(progress_data):
    """Sauvegarde le fichier de progression"""
    progress_file = Path(__file__).parent.parent / "PROGRESS_TRACKER.json"
    with open(progress_file, 'w') as f:
        json.dump(progress_data, f, indent=2)
    print(f"✅ Progression sauvegardée dans {progress_file}")

def update_subtask_status(progress_data, phase, step, subtask, new_status):
    """Met à jour le statut d'une sous-tâche"""
    if phase not in progress_data['phases']:
        raise ValueError(f"Phase {phase} non trouvée")
    
    if step not in progress_data['phases'][phase]['steps']:
        raise ValueError(f"Étape {step} non trouvée dans {phase}")
    
    if subtask not in progress_data['phases'][phase]['steps'][step]['subtasks']:
        raise ValueError(f"Sous-tâche {subtask} non trouvée dans {phase}.{step}")
    
    old_status = progress_data['phases'][phase]['steps'][step]['subtasks'][subtask]['status']
    progress_data['phases'][phase]['steps'][step]['subtasks'][subtask]['status'] = new_status
    
    # Ajouter timestamp si complété
    if new_status == 'completed':
        progress_data['phases'][phase]['steps'][step]['subtasks'][subtask]['completed_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"✅ {phase}.{step}.{subtask}: {old_status} → {new_status}")
    return True

def update_step_status(progress_data, phase, step, new_status):
    """Met à jour le statut d'une étape"""
    if phase not in progress_data['phases']:
        raise ValueError(f"Phase {phase} non trouvée")
    
    if step not in progress_data['phases'][phase]['steps']:
        raise ValueError(f"Étape {step} non trouvée dans {phase}")
    
    old_status = progress_data['phases'][phase]['steps'][step]['status']
    progress_data['phases'][phase]['steps'][step]['status'] = new_status
    
    # Ajouter timestamps
    if new_status == 'in_progress' and not progress_data['phases'][phase]['steps'][step].get('start_date'):
        progress_data['phases'][phase]['steps'][step]['start_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elif new_status == 'completed':
        progress_data['phases'][phase]['steps'][step]['end_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"✅ {phase}.{step}: {old_status} → {new_status}")
    return True

def recalculate_progress(progress_data):
    """Recalcule tous les pourcentages de progression"""
    for phase_id, phase_data in progress_data['phases'].items():
        if 'steps' not in phase_data:
            continue
            
        total_subtasks = 0
        completed_subtasks = 0
        
        for step_id, step_data in phase_data['steps'].items():
            if 'subtasks' in step_data:
                step_total = len(step_data['subtasks'])
                step_completed = sum(1 for subtask in step_data['subtasks'].values() 
                                   if subtask['status'] == 'completed')
                
                total_subtasks += step_total
                completed_subtasks += step_completed
                
                # Mettre à jour le statut de l'étape basé sur les sous-tâches
                if step_completed == 0:
                    step_status = 'not_started'
                elif step_completed == step_total:
                    step_status = 'completed'
                else:
                    step_status = 'in_progress'
                
                if step_data['status'] != step_status and step_status != 'in_progress':
                    step_data['status'] = step_status
        
        # Mettre à jour la progression de la phase
        phase_data['progress']['completed'] = completed_subtasks
        phase_data['progress']['total'] = total_subtasks
        phase_data['progress']['percentage'] = round((completed_subtasks / total_subtasks) * 100) if total_subtasks > 0 else 0
        
        # Mettre à jour le statut de la phase
        if completed_subtasks == 0:
            phase_data['status'] = 'not_started'
        elif completed_subtasks == total_subtasks:
            phase_data['status'] = 'completed'
        else:
            phase_data['status'] = 'in_progress'
    
    # Calculer progression globale
    total_all = sum(phase['progress']['total'] for phase in progress_data['phases'].values())
    completed_all = sum(phase['progress']['completed'] for phase in progress_data['phases'].values())
    overall_percentage = round((completed_all / total_all) * 100) if total_all > 0 else 0
    
    progress_data['project_info']['overall_progress'] = f"{overall_percentage}%"
    progress_data['project_info']['last_updated'] = datetime.now().strftime("%Y-%m-%d")
    
    print(f"📊 Progression globale: {completed_all}/{total_all} ({overall_percentage}%)")

def add_blocker(progress_data, description, severity, affects):
    """Ajoute un nouveau bloqueur"""
    blocker_id = f"blocker_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    new_blocker = {
        "id": blocker_id,
        "description": description,
        "severity": severity,
        "affects": affects if isinstance(affects, list) else [affects],
        "created_date": datetime.now().strftime("%Y-%m-%d"),
        "status": "open"
    }
    
    progress_data['current_blockers'].append(new_blocker)
    print(f"🚫 Bloqueur ajouté: {blocker_id}")

def resolve_blocker(progress_data, blocker_id):
    """Résout un bloqueur"""
    for blocker in progress_data['current_blockers']:
        if blocker['id'] == blocker_id:
            blocker['status'] = 'resolved'
            blocker['resolved_date'] = datetime.now().strftime("%Y-%m-%d")
            print(f"✅ Bloqueur résolu: {blocker_id}")
            return True
    print(f"❌ Bloqueur non trouvé: {blocker_id}")
    return False

def add_team_note(progress_data, author, note):
    """Ajoute une note d'équipe"""
    new_note = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "author": author,
        "note": note
    }
    
    progress_data['team_notes'].append(new_note)
    print(f"📝 Note ajoutée par {author}")

def show_status(progress_data):
    """Affiche l'état actuel du projet"""
    print("\n" + "="*60)
    print("📊 ÉTAT ACTUEL DU PROJET WIKITRANSLATEAI")
    print("="*60)
    
    # Info projet
    info = progress_data['project_info']
    print(f"📋 Nom: {info['name']}")
    print(f"🔢 Version: {info['version']}")
    print(f"📅 Dernière MAJ: {info['last_updated']}")
    print(f"🎯 Phase Actuelle: {info['current_phase']}")
    print(f"📊 Progression Globale: {info['overall_progress']}")
    
    print("\n" + "-"*40)
    print("📈 PROGRESSION PAR PHASE")
    print("-"*40)
    
    for phase_id, phase_data in progress_data['phases'].items():
        status_emoji = {
            'not_started': '🔴',
            'in_progress': '🟡', 
            'completed': '🟢'
        }.get(phase_data['status'], '⚪')
        
        print(f"{status_emoji} {phase_data['name']}: {phase_data['progress']['percentage']}% "
              f"({phase_data['progress']['completed']}/{phase_data['progress']['total']})")
    
    # Bloqueurs actifs
    active_blockers = [b for b in progress_data['current_blockers'] if b.get('status', 'open') == 'open']
    if active_blockers:
        print(f"\n🚫 BLOQUEURS ACTIFS: {len(active_blockers)}")
        for blocker in active_blockers:
            print(f"   • {blocker['id']}: {blocker['description']} ({blocker['severity']})")
    
    # Prochaines actions
    if progress_data['next_actions']:
        print(f"\n🎯 PROCHAINES ACTIONS:")
        for action in progress_data['next_actions']:
            priority_emoji = {'critical': '🔥', 'high': '⚡', 'medium': '📋', 'low': '📌'}.get(action['priority'], '📌')
            can_start = '✅' if action['can_start_immediately'] else '⏳'
            print(f"   {priority_emoji} {can_start} {action['action']} ({action['estimated_hours']}h)")
    
    print("\n" + "="*60)

def main():
    parser = argparse.ArgumentParser(description="Mettre à jour la progression WikiTranslateAI")
    parser.add_argument('--step', help="ID de l'étape (ex: step_1_1)")
    parser.add_argument('--subtask', help="ID de la sous-tâche (ex: 1_1_1)")
    parser.add_argument('--status', choices=['not_started', 'in_progress', 'completed', 'blocked'], 
                       help="Nouveau statut")
    parser.add_argument('--phase', default='phase_1', help="Phase (défaut: phase_1)")
    
    parser.add_argument('--add-blocker', help="Description du nouveau bloqueur")
    parser.add_argument('--blocker-severity', choices=['critical', 'high', 'medium', 'low'], 
                       default='medium', help="Sévérité du bloqueur")
    parser.add_argument('--blocker-affects', help="Étapes affectées par le bloqueur")
    
    parser.add_argument('--resolve-blocker', help="ID du bloqueur à résoudre")
    
    parser.add_argument('--add-note', help="Ajouter une note d'équipe")
    parser.add_argument('--author', default='Team', help="Auteur de la note")
    
    parser.add_argument('--show-status', action='store_true', help="Afficher l'état actuel")
    parser.add_argument('--recalculate', action='store_true', help="Recalculer toutes les progressions")
    
    args = parser.parse_args()
    
    # Charger les données
    progress_data = load_progress()
    
    # Afficher statut
    if args.show_status:
        show_status(progress_data)
        return
    
    # Ajouter bloqueur
    if args.add_blocker:
        affects = args.blocker_affects.split(',') if args.blocker_affects else []
        add_blocker(progress_data, args.add_blocker, args.blocker_severity, affects)
        save_progress(progress_data)
        return
    
    # Résoudre bloqueur
    if args.resolve_blocker:
        resolve_blocker(progress_data, args.resolve_blocker)
        save_progress(progress_data)
        return
    
    # Ajouter note
    if args.add_note:
        add_team_note(progress_data, args.author, args.add_note)
        save_progress(progress_data)
        return
    
    # Mettre à jour statut
    if args.status:
        if args.subtask:
            if not args.step:
                print("❌ --step requis avec --subtask")
                return
            update_subtask_status(progress_data, args.phase, args.step, args.subtask, args.status)
        elif args.step:
            update_step_status(progress_data, args.phase, args.step, args.status)
        else:
            print("❌ --step ou --subtask requis avec --status")
            return
    
    # Recalculer progression
    if args.recalculate or args.status:
        recalculate_progress(progress_data)
    
    # Sauvegarder
    save_progress(progress_data)

if __name__ == "__main__":
    main()