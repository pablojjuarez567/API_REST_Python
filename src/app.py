from bson import ObjectId
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/student_db"
mongo = PyMongo(app)


# Students
@app.route('/all_students', methods=['GET'])
def get_all_students():
    students = mongo.db.student.find()
    response = []
    for student in students:
        response.append({
            'id': str(student['_id']),
            'name': str(student['name'])
        })

    if not response:
        return not_found()

    return jsonify(response)


@app.route('/student/<id>', methods=['GET'])
def get_student(id):
    pipeline = [
        {
            '$lookup': {
                'from': 'company',
                'localField': 'company',
                'foreignField': '_id',
                'as': 'company'
            }
        },
        {
            '$lookup': {
                'from': 'teacher',
                'localField': 'teacher',
                'foreignField': '_id',
                'as': 'teacher'
            }
        },
        {
            '$match': {
                '_id': ObjectId(id)
            }
        }
    ]
    students = list(mongo.db.student.aggregate(pipeline))

    if not students:
        return not_found()

    student = students[0]

    activity_ids = student["activities"]
    activities = []
    for activity_id in activity_ids:
        activity = mongo.db.activity.find_one({"_id": activity_id["_id"]})
        if activity is not None:
            activities.append(activity)

    total_time_required = 0.0
    total_time_optional = 0.0

    for activity in activities:
        aux_time = float(activity['time'])
        aux_type = activity['type']

        if aux_type == 'Obligatorio':
            total_time_required += aux_time
        else:
            total_time_optional += aux_time

    response = {
        'id': str(student['_id']),
        'name': student['name'],
        'company': student['company'][0]['name'],
        'teacher': student['teacher'][0]['name'],
        'total_hours_to_do': student['total_hours_to_do'],
        'total_time_required_done': str(total_time_required),
        'total_time_optional_done': str(total_time_optional),
        'required_remaining_time': str(float(student['total_hours_to_do']) - total_time_required)
    }
    return jsonify(response)


# Company and Teacher
@app.route('/company', methods=['GET'])
def get_all_companies():
    companies = mongo.db.company.find()
    response = []
    for company in companies:
        response.append({
            'id': str(company['_id']),
            'name': company['name'],
        })
    if not response:
        return not_found()

    return jsonify(response)


@app.route('/teacher', methods=['GET'])
def get_all_teachers():
    teachers = mongo.db.teacher.find()
    response = []
    for teacher in teachers:
        response.append({
            'id': str(teacher['_id']),
            'name': teacher['name'],
        })
    if not response:
        return not_found()

    return jsonify(response)


# Activities
@app.route('/all_activities/<id>', methods=['GET'])
def get_all_activities(id):
    student = mongo.db.student.find_one({'_id': ObjectId(id)})

    if not student:
        return not_found()

    activity_ids = student["activities"]
    activities = []
    for activity_id in activity_ids:
        activity = mongo.db.activity.find_one({"_id": activity_id["_id"]})
        if activity is not None:
            activities.append(activity)

    response = [{
        'id': str(student['_id']),
        'name': student['name']
    }]

    for activity in activities:
        response.append({
            'id': str(activity['_id']),
            'type': activity['type'],
            'time': activity['time'],
        })

    return jsonify(response)


@app.route('/activity/<id>', methods=['GET'])
def get_activity(id):
    activities = mongo.db.activity.find()
    response = []
    for activity in activities:
        if activity['_id'] == ObjectId(id):
            response.append({
                'id': str(activity['_id']),
                'type': activity['type'],
                'date': activity['date'],
                'time': activity['time'],
                'description': activity['description']
            })
    if not response:
        return not_found()

    return jsonify(response)


@app.route('/activity/<id>', methods=['POST'])
def create_activity(id):
    student = mongo.db.student.find_one({'_id': ObjectId(id)})

    if not student:
        return not_found()

    typeWork = request.json['type']
    date = request.json['date']
    time = request.json['time']
    description = request.json['description']

    if typeWork and date and time and description:
        idActivity = mongo.db.activity.insert_one(
            {'type': typeWork, 'date': date, 'time': time, 'description': description}
        )

        mongo.db.student.update_one(
            {'_id': ObjectId(id)},
            {'$push': {'activities': {'_id': idActivity.inserted_id}}}
        )

        response = {
            'id': str(idActivity.inserted_id),
            'type': typeWork,
            'date': date,
            'time': time,
            'description': description
        }
        return response

    else:
        return not_found()


@app.route('/activity/<id>', methods=['PUT'])
def update_activity(id):
    typeWork = request.json['type']
    date = request.json['date']
    time = request.json['time']
    description = request.json['description']

    if typeWork and date and time and description:
        mongo.db.activity.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'type': typeWork, 'date': date, 'time': time, 'description': description}}
        )
        response = jsonify({
            'id': id,
            'type': typeWork,
            'date': date,
            'time': time,
            'description': description
        })
        response.status_code = 200
        return response

    else:
        return not_found()


@app.route('/activity/<id>', methods=['DELETE'])
def delete_activity(id):
    mongo.db.activity.delete_one({'_id': ObjectId(id)})
    response = jsonify({'message': 'Actividad ' + id + ' fue eliminada correctamente'})
    return response


@app.errorhandler(404)
def not_found(error=None):
    response = jsonify({
        'message': 'Recurso no encontrado: ' + request.url,
        'status': 404
    })
    response.status_code = 404
    return response


if __name__ == '__main__':
    app.run(debug=True)
